import sys
import socket
import struct
import time
__author__ = 'GuihaoLiang'

UN_SHORT_MAX = 65535
UN_LONG_MAX = 4294967295
UN_LONG = 4294967296
MSS = 576


def get_local_time():
    """convert time to yyyy/mm/dd hours:minutes:secs"""
    local_time = time.localtime()
    return "{0}/{1}/{2} {3}:{4}:{5} ".format(local_time[0], local_time[1], local_time[2],
                                             local_time[3], local_time[4], local_time[5])


# This is the GBN receiver without implementing the buffer because the underlying
# path to the sender is reliable, so there is no need to implement a buffer.
class Receiver:
    def __init__(self, file_name='receiver.txt', src_port_num=20000, dest_ip='localhost',
                 dest_port_num=20001, log_file_name='log_receiver.txt'):
        """
        UDP server initializer
        :param file_name: str
        :param src_port_num: int
        :param dest_ip: str
        :param dest_port_num: int
        :param log_file_name: str
        :return:
        """
        self.file_name = file_name
        self.src_port_num = src_port_num
        self.src_ip = socket.gethostbyname(socket.gethostname())
        self.dest_ip = dest_ip
        self.dest_port_num = dest_port_num
        self.log_file_name = log_file_name
        # the last pkt number received
        self.ack_num_to = 0
        self.ack_num_from = 0
        self.seq_num_to = 0
        self.seq_num_from = 0
        self.expect_num = 0
        # the pkt received
        self.pkt_recv = None
        self.fin = False

        # result
        self.total_byte_recv = 0
        self.total_seg_recv = 0
        self.valid_seg_recv = 0

        # create file objects
        try:
            self._log = open(self.log_file_name, 'a')
            self._log.write(get_local_time()+'log starts.\n')
        except ValueError as e:
            print e
        except IOError as e:
            print e
            print 'Can\'t log the operation, pls repair ur lap :)\n'

        try:
            self._recv = open(self.file_name, 'w')
        except ValueError as e:
            print e
            self._log.write(get_local_time() + str(e))
        except IOError as e:
            print e
            self._log.write(get_local_time() + str(e))
        # create socket objects
        self.client_socket = None
        self.receiver_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.receiver_socket.bind(('', self.src_port_num))

    def close_file(self):
        self._log.write(get_local_time()+'log closed.\n')
        self._log.close()
        self._recv.close()

    def recv_pkt(self):
        # recv may introduce exception and the client is not the same.
        self.total_seg_recv += 1
        self.pkt_recv, self.client_socket = self.receiver_socket.recvfrom(MSS)
        if self.pkt_recv == '':
            raise KeyboardInterrupt('The socket is down!')

    def is_corrupt(self):
        """
        check the checksum to make sure the pkt is complete
        :return: bool
        """
        # if self.pkt_recv is None:
        #     return False
        temp = self.pkt_recv
        byte_len = len(temp)
        self.total_byte_recv += byte_len
        if byte_len % 2:
            byte_len += 1
            temp += '\x00'

        checksum = 0
        for short in struct.unpack('!' + str(byte_len / 2) + 'H', temp):
            checksum += short
        if checksum > UN_SHORT_MAX:
            checksum %= (UN_SHORT_MAX + 1)

        if checksum == UN_SHORT_MAX:
            return True
        return False

    def unpack_tcp_seg(self):
        """
        unpack the tcp segment received, here the pkt is not corrupted.
        :return: str
        """
        length = len(self.pkt_recv)
        header = struct.unpack('!2H2L4H', self.pkt_recv[0:20])
        print header
        if not self.fin:
            self._log.write(get_local_time() + '[ACK.] [SRC]: %s, %-6d, [DEST]: %s, %-6d, Sequence : %d, ACK : %d, '
                            % (self.src_ip, header[0], self.dest_ip, header[1], header[2], header[3]) +
                            'ack: %-2d, fin: %-2d' % (0, self.fin) + '\n')
        # self.dest_port_num = header[0]
        # if it's not the FIN and iff the ack_num is equal to the sequence number
        if not self.fin and self.expect_num == header[2]:
            self.valid_seg_recv += 1
            # h_len = header[4] >> 12
            h_len = 20
            dat_len = length - h_len
            # here we do not handle with the option field.
            # the ack_num is always the latest seq num received
            # print header[2]
            self.fin = header[4] % 2
            if self.fin:
                self._log.write(get_local_time() + '[ACK.] [SRC]: %s, %-6d, [DEST]: %s, %-6d, Sequence : %d, ACK : %d, '
                            % (self.src_ip, header[0], self.dest_ip, header[1], header[2], header[3]) +
                            'ack: %-2d, fin: %-2d' % (0, self.fin) + '\n')
                # this sentence will push the last sentence from stdout to file
                print 'Delivery completed successfully.\n'
                print 'Total bytes received = %d' % self.total_byte_recv
                print 'Segments received = %d' % self.total_seg_recv
                print 'Segments written = %d' % (self.valid_seg_recv - 1)
                # if a fin is received
                return ''

            self.ack_num_to = header[2]
            self.expect_num += 1
            if self.expect_num > UN_LONG_MAX:
                self.expect_num = 0

            return struct.unpack('!' + str(dat_len) + 's', self.pkt_recv[h_len:])[0]



    def pack_tcp_seg(self, ack, fin, seq_num_to, ack_num_to, segment, h_len=5):
        """
        make the tcp segment wrap with header
        :param h_len: int # range [20,31)
        :param ack: bool
        :param fin: bool
        :param segment : str
        :return: str
        """
        # form the Header length row
        h_len <<= 12
        ack <<= 4
        h_len += ack + fin
        h_len %= (UN_SHORT_MAX + 1)

        seg_len = len(segment)
        # the segment length must be even, if not, padding a '\x00'
        if seg_len % 2:
            seg_len += 1
        seg_stream = struct.pack('!'+str(seg_len)+'s', segment)
        # add all the data and header field
        checksum = 0
        for short in struct.unpack('!'+str(seg_len/2)+'H', seg_stream):
            checksum += short

        # truncate the seq_num sent
        if seq_num_to > UN_LONG_MAX:
            seq_num_to %= UN_LONG

        # truncate the ack num
        if ack_num_to > UN_LONG_MAX:
            ack_num_to %= UN_LONG

        # Urgent data pointer and receive window field is 0
        checksum += self.src_port_num + self.dest_port_num + (seq_num_to >> 16) + seq_num_to + \
                    (ack_num_to >> 16) + ack_num_to + h_len
        # omit the high position bits
        if checksum > UN_SHORT_MAX:
            checksum %= (UN_SHORT_MAX+1)
        # ones complement
        checksum = UN_SHORT_MAX - checksum

        self._log.write(get_local_time() + '[SENT] [SRC]: %s, %-6d, [DEST]: %-s, %-6d, Sequence : %d, ACK : %d, ' %
                        (self.src_ip, self.src_port_num, self.dest_ip, self.dest_port_num, seq_num_to, ack_num_to) +
                        'ack: %-2d, fin: %-2d' % (ack, fin) + '\n')

        return struct.pack('!2H2L4H', self.src_port_num, self.dest_port_num, seq_num_to, ack_num_to,
                           h_len, 0, checksum, 0) + segment

    def send_ack(self):
        if not self.fin:
            self.receiver_socket.sendto(self.pack_tcp_seg(1, 0, self.seq_num_to,
                                                          self.ack_num_to, ''), (self.dest_ip, self.dest_port_num))
        else:
            self.receiver_socket.sendto(self.pack_tcp_seg(0, 1, self.seq_num_to,
                                                          self.ack_num_to, ''), (self.dest_ip, self.dest_port_num))
            self.close_file()

    def write(self):
        # lack the log
        # the recv must be executed before the is_corrupt()
        self.recv_pkt()
        if self.is_corrupt() and not self.fin:
            seg = self.unpack_tcp_seg()
            if seg:
                self._recv.write(seg)
            # whenever a pkt arrives, an ack is sent.
            # avoid the first pkt corrupt and ack 0 back. if the first seq 0 corrupt, no reply.
            # also, if expect_num change from UN_LONG to 0, the instruction below still applies.
            if self.ack_num_to != self.expect_num:
                self.send_ack()

if __name__ == '__main__':
    print 'Press ctrl + C to exit.\n'
    try:
        receiver = Receiver(sys.argv[1], int(sys.argv[2]), sys.argv[3], int(sys.argv[4]), sys.argv[5])
        # receiver = Receiver()
        while True:
            receiver.write()
    except KeyboardInterrupt:
        try:
            # Stop the sender.
            receiver.fin = True
            receiver.send_ack()
            print 'Terminated by user, additional fin sent to stop the sender.\n'
            receiver.close_file()
            receiver.receiver_socket.close()
        except ValueError:
            print 'File already closed.\n'
    except TypeError, e:
        print e
        print 'port number must be integer.\n'
        sys.exit(35)
