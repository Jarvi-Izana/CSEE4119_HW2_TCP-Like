While running, the console will print out the header, ack number and base number. 

1, DESCRIPTION OF THE CODE
>>>1.0 Basic method shared by two .py
I should have employed inherit to do this instead of reusing it again and again.
-> def pack_tcp_seg():
pack string with header into byte stream.
->def is_corrupt():
determine the whether the checksum of packet is correct.

>>>1.1 TCP_sender.py
    This code is mainly on the GBN but it's a hybrid of the TCP protocol. The sender has buffer and timer for all the
packet on transmission. And use the TCP RTT estimation method to compute RTT. The difference is the retransmission part,
here we retransmit all the packets in the buffer if there is no timeout when retransmission. As we know, the GBN is
somewhat low efficient. The code has three parts, the first is to send the packet, second is to handle the acknowledgement,
and the third is to retransmit. All the seq num is based on a ring of pow(2,32). If the seq num exceeds the maximum
UN_LONG = 4294967296, the seq %= UN_LONG. And this mechanism is also applied to the calculation of checksum since it
can't exceed UN_SHORT_MAX = 65535, so checksum %= UN_SHORT_MAX.

# truncate the seq_num sent
if seq_num_to > UN_LONG_MAX:
    seq_num_to %= UN_LONG
# truncate the ack num
  if ack_num_to > UN_LONG_MAX:
    ack_num_to %= UN_LONG

if checksum > UN_SHORT_MAX:
   checksum %= (UN_SHORT_MAX + 1)

The most hard part is at the edge of the pow(2,16) ring, that is, when the seq is big enough and be converted into 0 again,
and the base is 65535, the offset between the base and next is not 0 - 65535 but 0 + pow(2, 16) - 65535.
# assume the ack will arrive in order and without loss
    if self._base > self._high and self.ack_num_from < self._low:
        offset = self.ack_num_from + pow(2, 16) - self._base
    else:
        offset = self.ack_num_from - self._base

>>1.1.0 timer
>def estimate_interval(self)
This is the same with the TCP RTT estimation method.
>def is_timeout(self)
        diff = time.time() - self.current_pkt_time
        # time out
        if diff >= self.timeout_interval:
            # close the timer
            self.timer_on = False
            if self.first_RTT:
                self.timeout_interval *= 2
            return True
        return False

The self.first_RTT is the flag to apply slow start mechanism. If the first packet is not received, the sender will double
the current time out interval until you can get the first sample RTT.

>>1.1.1 send packets

First use the module struct to pack the the segments into byte stream.
->def pack_tcp_seg(self, ack, fin, seq_num_to, ack_num_to, segment, h_len=5)

Then combine the window size to retransmit the packet.
->def sendto(self): while send the segments, the sender also has to put segments sent into a buffer for retransmission.
Also store the time when send a segment so you can trace all the send time to corresponding segments. All this buffer is
dynamically changed but with the max size of window size: self._buffer[self._next_seq_num - self._base] = content.
This sender can be interrupted by the outside handle_tcp_ack() and is_timeout().

And this method can realize the fast recovery from last time sending by detecting whether current next_seq_num < base.

>>1.1.2 receive ack and handle with it

->def handle_tcp_ack(self):
This method is concurrently running with the sender because it will change the base all the time and allow the sender to
send packet simultaneously. And when valid ack comes, it will pop out the time in the timer buffer to update the time for
the oldest packet sent but not yet acked. Also, pop out the acked content to update the buffer which stores the current sent
packets for the aim of retransmission.

This method is dedicate designed with function with detection 3 duplicate ack and decide to estimate the sample RTT when
the ack num equals the base, that is estimate time for the oldest sent but not not acked packets.

>>1.1.3 retransmission
-> def retransmit(self):
The method is used to retransmit the segments with index from base to nextToSend-1. And it will recursively be invoked
when timeout at retransmission procedure. This method is similar with all the method above, can be interrupted by the
time out. When in retransmission mode, the sender cannot send any packet.


>>>1.2 TCP_receiver.py
The receiver is simpler to the sender because I'm not going to add buffer to receiver. All the methods are slightly different
with the sender but the principle is the same.
>>1.2.1 def unpack_tcp_seg(self):
This method will handle with hose packets uncorrupted. If the current sent packet's sequence number is not the number of
sequence expected, the receiver will discard that. This is consistent with GBN receiver.

Also, the pit fall is at if ack number equals to expect number, it means the first pkt lost, so here we don't reply.

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

The second part is, we let ack number equal to header[3], that is the seq number of the TCP header. So we don't have to
convert the ack number to 0 if it exceeds the max of 32 bits long integer.

2, DETAILS AND DEVELOPMENT ENVIRONMENT
MAC OSX
python 2.7.10

3, INSTRUCTION ON HOW TO RUN YOUR CODE
# start the proxy under instruction of that, here we set src port as 20001 and destination port is 20000
./newudpl -ilocalhost/20001 -olocalhost/20000 -v -d0.01 -B5 -L5 -O5

# the first two args are python <.py>
python TCP_sender.py <filename to send> <dest ip> <dest port num> <src port num> <log file name> <window size>
python TCP_receiver.py <file to receive> <src port num> <dest ip> <dest port num> <log file name>

4, SIMPLE COMMANDS TO INVOKE YOUR CODE
# sample
$ ./newudpl -ilocalhost/20001 -olocalhost/20000 -v -d0.01 -B5 -L5 -O5
$ python TCP_sender.py sender.txt localhost 41192 20001 log_sender.txt 5
$ python TCP_receiver.py receiver.txt 20000 localhost 20001 log_receiver.txt

# explanation
# the proxy will transmit the packet from 20001 to 20000
./newudpl -ilocalhost/20001 -olocalhost/20000 -v -d0.01 -B5 -L5 -O5

# if you don't fist run the receiver, it will generate very low start.
# 41192/41193 is target port number, and it is the default port number of the proxy.
# the src port number is 20001, the localhost ip is get from socket.getbyhostname(socket.gethostname())
python TCP_sender.py sender.txt localhost 41192 20001 log_sender.txt 5

# the src port is the 20000, and the target port number is 20001
python TCP_receiver.py receiver.txt 20000 localhost 20001 log_receiver.txt

5, ADDITIONAL FUNCTION AND HOW TO TEST

>>>Fast recovery:
you can terminate the sender while sending is not competed. Then restart the sender, the program will fast recover
according to the ack received and continue the last time's sending.

CTRL + C the sender when sending, and restart it.

>>>Arbitrary order of start:
you can start either receiver or sender first. Only for the start. If you want to kill the receiver and restart it again, pls end the sender first.
And the log file will log the stop behavior by itself (completed) or receiver(interrupted).


