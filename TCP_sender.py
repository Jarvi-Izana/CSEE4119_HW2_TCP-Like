import socket
import struct
import time
import sys
from threading import Thread
from threading import ThreadError

__author__ = 'GuihaoLiang'

UN_SHORT_MAX = 65535
UN_LONG_MAX = 4294967295
UN_LONG = 4294967296
FIN = 1
MSS = 576
ALPHA = 0.125
BETA = 0.25


def get_local_time():
    """convert time to yyyy/mm/dd hours:minutes:secs"""
    local_time = time.localtime()
    return "{0}/{1}/{2} {3}:{4}:{5} ".format(local_time[0], local_time[1], local_time[2],
                                             local_time[3], local_time[4], local_time[5])


class Sender:
    def __init__(self, file_name='sender.txt', dest_ip='localhost', dest_port_num=41192,
                 src_port_num=20001, log_file_name='log_sender.txt', window_size=3):
        """
        UDP client initializer
        :param file_name: str
        :param dest_ip: str
        :param dest_port_num: int
        :param src_port_num: int
        :param log_file_name: str
        :param window_size: int
        :return: None
        """
        self.file_name = file_name
        # destination port ip
        self.dest_ip = dest_ip
        # destination port number
        self.dest_port_num = dest_port_num
        self.src_port_num = src_port_num
        self.src_ip = socket.gethostbyname(socket.gethostname())
        self.log_file_name = log_file_name
        # window size should smaller than the half of the finite seq num
        self.window_size = window_size
        self._buffer = [''] * window_size
        self._buffer_RTT = []
        self.ack_recv = ''
        # ring edge
        self._high = UN_SHORT_MAX - window_size + 1
        self._low = window_size
        # header parameters #
        self.seq_num_to = 0
        self.seq_num_from = 0
        self.ack_num_from = 0
        self.ack_num_to = 0
        # initialize the client socket #
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_socket.bind(('', self.src_port_num))
        # private vars #
        self._duplicate = 0
        self._dup_flag = False
        self._base = 0
        self._next_seq_num = 0
        self._MSS = MSS
        self._timeout = False
        # timer
        self.current_pkt_time = time.time()
        self.sample_RTT = 1
        self.estimated_RTT = 1
        self.dev_RTT = 0
        self.timeout_interval = 1
        self.timer_on = False
        # flags
        self.first_RTT = True
        self.FIN = False
        self.fin_ack = False
<<<<<<< HEAD
        self.stop_by_receiver = True
=======
>>>>>>> 52282acb4249355a0d6b65c28b0089014db0c564
        # log
        self.retrans_num = 0
        self.retrans_seg_num = 0
        self.total_byte_sent = 0
<<<<<<< HEAD
        self.total_seg_sent = 0
=======
>>>>>>> 52282acb4249355a0d6b65c28b0089014db0c564
        # status
        self.retrans_status = False

        # initialize the file objects of send and log #
        try:
            self._log = open(self.log_file_name, 'a')
            self._log.write(get_local_time() + ' log starts.\n')
        except ValueError as e:
            print e
        except IOError as e:
            print e
            print 'Can\'t log the operation, pls repair ur lap :)\n'

        try:
            self._file = open(self.file_name, 'r')
            # print self._file.read(100)
        except ValueError as e:
            print e
        except IOError as e:
            print e
<<<<<<< HEAD
            sys.exit('can\'t open file, pls check the file path and name.\n')
=======
>>>>>>> 52282acb4249355a0d6b65c28b0089014db0c564

    def close_file(self):
        """
        close the file object when transmission is completed or interrupted
        :return: None
        """
        self._file.close()
<<<<<<< HEAD
        if self.stop_by_receiver:
            self._log.write(get_local_time() + 'STOP BY RECEIVER.\n')
        else:
            self._log.write(get_local_time() + 'COMPLETED.\n')
=======
>>>>>>> 52282acb4249355a0d6b65c28b0089014db0c564
        self._log.write(get_local_time() + ' log closed.\n')
        self._log.flush()
        self._log.close()

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
        # h_len %= (UN_SHORT_MAX + 1)
<<<<<<< HEAD
        self.total_seg_sent += 1
        seg_len = len(segment)
        self.total_byte_sent += (seg_len + 20)
=======

        seg_len = len(segment)
>>>>>>> 52282acb4249355a0d6b65c28b0089014db0c564
        # the segment length must be even, if not, padding a '\x00'
        if seg_len % 2:
            seg_len += 1
        seg_stream = struct.pack('!' + str(seg_len) + 's', segment)
        # add all the data and header field
        checksum = 0

        for short in struct.unpack('!' + str(seg_len / 2) + 'H', seg_stream):
            checksum += short
        # print 'without header ' + str(checksum)
        # truncate the seq_num sent
        if seq_num_to > UN_LONG_MAX:
            seq_num_to %= UN_LONG
        # truncate the ack num
        if ack_num_to > UN_LONG_MAX:
            ack_num_to %= UN_LONG

        # Urgent data pointer and receive window field is 0
        temp = self.src_port_num + self.dest_port_num + (seq_num_to >> 16) + \
                                    seq_num_to + (ack_num_to >> 16) + ack_num_to + h_len
        # print 'headerSum ' + str(temp)
        checksum += temp
        # omit the high position bits
        if checksum > UN_SHORT_MAX:
            checksum %= (UN_SHORT_MAX + 1)
        # ones complement
        checksum = UN_SHORT_MAX - checksum

        self._log.write(get_local_time() + '[SENT] [SRC]: %s, %-6d, [DEST]: %-s, %-6d, Sequence : %d, ACK : %d, ' %
                        (self.src_ip, self.src_port_num, self.dest_ip, self.dest_port_num, seq_num_to, ack_num_to) +
                        'ack: %-2d, fin: %-2d, EstimatedRTT: %10.4f' % (ack, fin, self.estimated_RTT) + '\n')
        return struct.pack('!2H2L4H', self.src_port_num, self.dest_port_num, seq_num_to, ack_num_to,
                            h_len, checksum, 0, 0) + segment
        # print len(seg)
        # ch = 0
        # for short in struct.unpack('!288H', seg):
        #     ch += short
        #
        # print 'ch: ' + str(ch % (UN_SHORT_MAX + 1))
        # return 'hehe'

    def recv_pkt(self):
        self.ack_recv = self.client_socket.recv(20)

    def is_corrupt(self):
        """
        check the checksum to make sure the ack pkt is complete
        :return: bool
        """
        # if self.ack_recv is None:
        #     return False
        byte_len = len(self.ack_recv)
        checksum = 0
        for short in struct.unpack('!' + str(byte_len / 2) + 'H', self.ack_recv):
            checksum += short

        if checksum > UN_SHORT_MAX:
            checksum %= (UN_SHORT_MAX + 1)

        if checksum == UN_SHORT_MAX:
            return True

        return False

    def start_timer(self):
        self.timer_on = True
        self.current_pkt_time = time.time()

    def is_timeout(self):
        """
        if time out return True
        :return: bool
        """
        diff = time.time() - self.current_pkt_time
        # time out
        if diff >= self.timeout_interval:
            # close the timer
            self.timer_on = False
            if self.first_RTT:
                self.timeout_interval *= 2
            return True
<<<<<<< HEAD
=======

>>>>>>> 52282acb4249355a0d6b65c28b0089014db0c564
        return False

    def send_time_buffer(self):
        self._buffer_RTT.append(time.time())

    def estimate_interval(self):
        """
        :return: bool
        """
        if self.first_RTT:
            self.estimated_RTT = self.sample_RTT
            self.first_RTT = False
        else:
            try:
                self.sample_RTT = time.time() - self._buffer_RTT.pop(0)
                # print 'sample: ' + str(self.sample_RTT)
            except IndexError as e:
                # print get_local_time() + str(e) + ' contention of threads occurs.\n'
                if self.retrans_status:
                    return True
                else:
                    return False

        self.estimated_RTT = (1 - ALPHA) * self.estimated_RTT + ALPHA * self.sample_RTT
        self.dev_RTT = (1 - BETA) * self.dev_RTT + BETA * abs(self.sample_RTT - self.estimated_RTT)
        self.timeout_interval = self.estimated_RTT + 4 * self.dev_RTT
        # print 'interval :' + str(self.timeout_interval)
        return False

    def sendto(self):
        # if the _base exceeds the UN_LONG ring, then reset.
        if self._base > UN_LONG_MAX:
            self._next_seq_num -= UN_LONG
            self._base -= UN_LONG
        boundary = self._base + self.window_size
        while self._next_seq_num < boundary and not self.FIN:
            # read 576-20 bytes
            content = self._file.read(self._MSS-20)
            if content:
<<<<<<< HEAD
                if self._next_seq_num < self._base:
                    self._next_seq_num += 1
                    self.start_timer()
                    continue
                self._buffer[self._next_seq_num - self._base] = content
=======
                self._buffer[self._next_seq_num - self._base] = content
                self.total_byte_sent += len(content)
>>>>>>> 52282acb4249355a0d6b65c28b0089014db0c564
                # set the seq num
                if self._next_seq_num > UN_LONG_MAX:
                    self.seq_num_to = self._next_seq_num % UN_LONG
                else:
                    self.seq_num_to = self._next_seq_num
                # point to next position of buffer
                self._next_seq_num += 1
                if not self.timer_on:
                    self.start_timer()
                # store the corresponding time
                self.send_time_buffer()
                self.client_socket.sendto(self.pack_tcp_seg(0, 0, self.seq_num_to, self.ack_num_to, content),
                                          (self.dest_ip, self.dest_port_num))
            else:
                self.FIN = True
<<<<<<< HEAD
                self.stop_by_receiver = False
                try:
                    self._buffer[self._next_seq_num - self._base] = self.FIN
                except IndexError, e:
                    print 'transmission already completed.\n'
=======
                self._buffer[self._next_seq_num - self._base] = self.FIN
>>>>>>> 52282acb4249355a0d6b65c28b0089014db0c564
                self.seq_num_to = self._next_seq_num
                self.send_time_buffer()
                self.client_socket.sendto(self.pack_tcp_seg(0, 1, self.seq_num_to, self.ack_num_to, ''),
                                              (self.dest_ip, self.dest_port_num))

            if self.is_timeout() or self.retrans_status:
                self.retransmit()
                break

    def handle_tcp_ack(self):
        """
        unpack the tcp segment received, here the pkt is not corrupted.
        :return: str
        """
        # length = len(self.ack_recv)
        self.recv_pkt()
        if self.ack_recv:
            header = struct.unpack('!2H2L4H', self.ack_recv[0:20])
            # print header
            self._log.write(get_local_time() + '[ACK.] [SRC]: %s, %-6d, [DEST]: %s, %-6d, Sequence : %d, ACK : %d, '
                            % (self.src_ip, header[0], self.dest_ip, header[1], header[2], header[3]) +
                            'ack: %-2d, fin: %-2d, EstimatedRTT: %10.4f' % (0, self.fin_ack, self.estimated_RTT) + '\n')

            # self.dest_port_num = header[0]
            # if it's not the FIN and iff the ack_num is equal to the sequence number
            if header[4] % 2:
                self.fin_ack = True
                self._log.write(get_local_time() + '[ACK.] [SRC]: %s, %-6d, [DEST]: %s, %-6d, Sequence : %d, ACK : %d, '
                            % (self.src_ip, header[0], self.dest_ip, header[1], header[2], header[3]) +
                            'ack: %-2d, fin: %-2d, EstimatedRTT: %10.4f' % (0, self.fin_ack, self.estimated_RTT) + '\n')
                self.close_file()
                return

            if (header[4] >> 4) % 2:
                self.ack_num_from = header[3]
<<<<<<< HEAD
                print 'base num:%-5d' % self._base
                print 'ack. num:%-5d' % header[3]
=======
                print 'base number: ' + str(self._base)
                print 'ack number: ' + str(header[3])
>>>>>>> 52282acb4249355a0d6b65c28b0089014db0c564

            # assume the ack will arrive in order and without loss
            if self._base > self._high and self.ack_num_from < self._low:
                offset = self.ack_num_from + UN_LONG - self._base
            else:
                offset = self.ack_num_from - self._base

            if offset >= 0:
                # pop out the buffer that already received
                for i in xrange(offset + 1):
<<<<<<< HEAD
                    try:
                        self._buffer.pop(0)
                        self._buffer.append('')
                    except IndexError:
                        pass
=======
                    self._buffer.pop(0)
                    self._buffer.append('')
>>>>>>> 52282acb4249355a0d6b65c28b0089014db0c564

                self._base += 1 + offset
                # get the RTT time for further estimation.
                if not self._dup_flag and offset == 0:
<<<<<<< HEAD
                    # to determine whether the sender is retransmitting
                    # because when retransmitting, the time buffer will be cleared.
                    # also when in fast recovery mode, the time buffer is empty too,
                    # so the time should not be evaluated.
=======
>>>>>>> 52282acb4249355a0d6b65c28b0089014db0c564
                    if self.estimate_interval():
                        return
                # start the timer for next pkt
                self.start_timer()
                self._duplicate = 0
                self._dup_flag = False
            elif offset == -1:
                self._duplicate += 1
                # this place is very excellent design here, avoid many duplicate here.
                if self._duplicate % self.window_size == 2:
                    self._dup_flag = True
                    # interrupt the sender then retransmit
                    self.retrans_status = True
                    # self.retransmit() can't use this because it

    def retransmit(self):
        try:
            # print (self._base, self._next_seq_num)
            self.retrans_status = True
            self.retrans_num += 1
            # print 'retransmitted times: ' + str(self.retrans_status) + ' ' + str(self.retrans_num)
            # retransmit the pkt and restart the timer.
            self.start_timer()
            # clear the buffer because the content is retransmitted
            # the RTT won't be estimated for retransmitted pkt
            self._buffer_RTT = []
            temp = self._base
            offset = 0
            content_buffer = self._buffer[:]
            for content in content_buffer:
                if content:
                    self.send_time_buffer()
                    if content == self.FIN:
                        self.client_socket.sendto(self.pack_tcp_seg(0, 1, temp + offset, 0, ''),
                                              (self.dest_ip, self.dest_port_num))
                    else:
                        self.client_socket.sendto(self.pack_tcp_seg(0, 0, temp + offset, 0, content),
                                              (self.dest_ip, self.dest_port_num))
                    offset += 1
                    if self.is_timeout():
                        self.retransmit()
                        break
                break

            self.retrans_seg_num += offset
            self.retrans_status = False

<<<<<<< HEAD
            # print 'retransmission ends.'
=======
            print 'retransmission ends.'
>>>>>>> 52282acb4249355a0d6b65c28b0089014db0c564
            return
        except RuntimeError, e:
            print 'Link is broken or target can\'t be connected.\n' + e
            self.close_file()
            self.client_socket.close()
            sys.exit(-1)

    def send_file(self):
        print get_local_time() + 'Transmission started.\n'
        while not self.fin_ack:
            self.sendto()
            if self.is_timeout() or self.retrans_status:
<<<<<<< HEAD
                # print 'time out by outside.'
                self.retransmit()

        if self.stop_by_receiver:
            print get_local_time() + 'Transmission Stopped by receiver.\n'
        else:
            print get_local_time() + 'Transmission completed.\n'

        print 'Total bytes sent = %d' % self.total_byte_sent
        print 'Total segments sent = %d' % self.total_seg_sent
        print 'segments successfully received by %s = %d' % (self.dest_ip, self._next_seq_num)
        # print 'segments retransmitted: %d' % self.retrans_seg_num
        print 'segments retransmitted: %d' % abs(self.total_seg_sent - self._next_seq_num)

    def handle_ack(self):
        while not self.fin_ack:
            # if not self.is_timeout
=======
                print 'time out by outside.'
                self.retransmit()

        print get_local_time() + 'Transmission completed.\n'
        print 'Total bytes sent = %-10d' % self.total_byte_sent
        print 'segments sent = %-10d' % (self._next_seq_num - 1)
        print 'segments retransmitted: %-10d' % self.retrans_seg_num

    def handle_ack(self):
        while not self.fin_ack:
            # if not self.is_timeout():
>>>>>>> 52282acb4249355a0d6b65c28b0089014db0c564
            self.handle_tcp_ack()


if __name__ == '__main__':
    try:
        sender = Sender(sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]),
                        sys.argv[5], int(sys.argv[6]))
<<<<<<< HEAD
        # sender = Sender()
        # this is fatal mistake, the target should be the reference to your func or method:
        # ack_handler = Thread(target=sender.handle_ack()), by this way, it won't prompt any instruction
        # to make you know that sth is wrong.
=======
>>>>>>> 52282acb4249355a0d6b65c28b0089014db0c564
        ack_handler = Thread(target=sender.handle_ack)
        ack_handler.setDaemon(True)
        ack_handler.start()

        snd_handler = Thread(target=sender.send_file)
        snd_handler.setDaemon(True)
        snd_handler.start()

    except ThreadError, e:
        print 'Fail to open thread. Error: #{0}, {1}'.format(str(e[0]), e[1])
        sys.exit('Thread Fail')

    print 'When transmission completed, press Ctrl + C to exit.'
    try:
        while True:
<<<<<<< HEAD
            time.sleep(1)
=======
            time.sleep(0.01)
>>>>>>> 52282acb4249355a0d6b65c28b0089014db0c564
    except KeyboardInterrupt:
        print 'main process terminated by user.\n'
        sys.exit(27)

    except TypeError, e:
        print e
        print 'port number must be integer.\n'
        sys.exit(35)
<<<<<<< HEAD
    except:
        print 'Pls restart the program, system inner error detected.\n'
        sys.exit(-1)
=======
>>>>>>> 52282acb4249355a0d6b65c28b0089014db0c564
