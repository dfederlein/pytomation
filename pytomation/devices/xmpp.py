import ssl

from sleekxmpp import ClientXMPP
from sleekxmpp.xmlstream import cert

from pytomation.devices import Door, StateDevice, State
from pytomation.interfaces import Command

class XMPP(StateDevice):
    STATES = [State.UNKNOWN, State.ON, State.OFF]
    COMMANDS = [Command.MESSAGE]

    def __init__(self, *args, **kwargs):
        super(XMPP, self).__init__(*args, **kwargs)

    def _initial_vars(self, *args, **kwargs):
        super(XMPP, self)._initial_vars(*args, **kwargs)
        self._id = kwargs.get('id',None)
        self._password = kwargs.get('password', None)
        self._server = kwargs.get('server', None)
        self._port = kwargs.get('port', None)

        self._xmpp = ClientXMPP(self._id, self._password)

        self._xmpp.add_event_handler("session_start", self._session_start)
        self._xmpp.add_event_handler("message", self._message)
        self._xmpp.add_event_handler("ssl_invalid_cert", self._invalid_cert)

        self._logger.info('Connecting to server for id:{id} ({server})'.format(
                                               id=self._xmpp._id,
                                               server=self._server,
                                                                               ))
        status = None
        if self._server or self._port:
            status = self._xmpp.connect((self._server, self._port))
        else:
            status = self._xmpp.connect()
        self._logger.info("Connection Result: {0}".format( status))

        self._xmpp.process(block=False)
        self._logger.debug('Processing')
        
    def _session_start(self, event):
        self._xmpp.send_presence()
        self._xmpp.get_roster()
        
    def _message(self, msg):
        if msg['type'] in ('chat', 'normal'):
            msg.reply("Thanks for sending\n%(body)s" % msg).send()


    def _invalid_cert(self, pem_cert):
        der_cert = ssl.PEM_cert_to_DER_cert(pem_cert)
        try:
            cert.verify('talk.google.com', der_cert)
            logging.debug("CERT: Found GTalk certificate")
        except cert.CertificateError as err:
            log.error(err.message)
            self.disconnect(send_close=False)

    def _delegate_command(self, command, *args, **kwargs):
        if isinstance(command, tuple) and command[0] == Command.MESSAGE:            
            result = self._xmpp.send_message(mto=command[1],
                                      mbody=command[2],
                                      mtype='chat')
        super(XMPP, self)._delegate_command(command, *args, **kwargs)

        
    