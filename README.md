====== Simple XMPP load test tool =====

Requirements:
    python >= 3.2, python >= 2.7

Installation:
    python setup.py install

Purposes:
    Program read file with users and passwords with even count of lines. 
    Then it makes split users to senders and receivers. Users count \ 2 
    Then it puts each client in it's worker in separate thread (-w option). Number threads for worker is clients count / workers count
    Then it runs tests:
        1. Add sender and receiver to contact list to each other
        2. Send messages beetween senders and receivers each interval (-i option). Receiver answers for a message
        3. Change status for sender each intervel (-i option)
        4. Run send and change statuses cycle for a runs count (-r option)
        5. Remove sender and receiver from contact list for each over

Notes:
    For best perfomance use large value of workers

Run:
    xmpptest -f list_of_users -i 10 -r 1 -q -w 1

Help:
    xmpptest -h
