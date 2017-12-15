#!/usr/bin/env python
#

import sys, argparse, logging, re, numpy


def computeMetrics(filename):
    eventPosts = ackPolls = 0 # outgoing event posts and ack polls
    emptyEventChecks = healthEndpointChecks = ackChecks = 0 # health and preflight check outgoing request counts
    lbSpins = channelBecameAvailable = channelBecameUnavailable = eventPostServerBusy = ackPollServerBusy = genericServerBusy = 0 # back pressure
    ackTimesMS = [] # list of times taken to acknowledge a batch
    numAcksReceivedInRequest = []
    numAckIDsInRequest = []
    numAcksReceivedWhenAtLeastOneReceived = []
    responseTimes = []
    cookieViolations = 0 # sticky session violations

    file = open(filename, "r")

    logging.info("Computing metrics on file " + filename)

    for line in file:
        if re.search("executing event batch post.*", line):
            eventPosts += 1

        if re.search("executing ack poll request.*", line):
            ackPolls += 1

        if re.search("executing empty event post.*", line):
            emptyEventChecks += 1

        if re.search("executing poll on health endpoint.*", line):
            healthEndpointChecks += 1

        if re.search("executing ack check.*", line):
            ackChecks += 1

        if re.search("load balancer waited 1.*", line):
            lbSpins += 1

        if re.search("to change the Session-Cookie.*", line):
            cookieViolations += 1

        if re.search("503 response from event.*", line):
            eventPostServerBusy += 1

        if re.search("503 response from ack.*", line):
            ackPollServerBusy += 1

        if re.search("503 response in HttpCallbacksGeneric.*", line):
            genericServerBusy += 1

        if re.search("channel became unavailable.*", line):
            channelBecameUnavailable += 1

        if re.search("channel became available.*", line):
            channelBecameAvailable += 1

        # response times
        match = re.search("Response received\. .* took ([0-9]+) ms.*", line)
        if match:
            responseTimes.append(match.group(1))

        # acknowledged callback invocation
        match = re.search("byte batch acknowledged in ([0-9]+) ms", line)
        if match:
            ackTimesMS.append(match.group(1))

        # successful ack response
        match = re.search("received success on ([0-9]+) ack ids out of ([0-9]+).*", line)
        if match:
            numAcksReceivedInRequest.append(match.group(1))
            numAckIDsInRequest.append(match.group(2))

            if (int(match.group(1)) > 0):
                numAcksReceivedWhenAtLeastOneReceived.append(match.group(1))

    # convert to numpy array with all numeric types
    responseTimes = numpy.array(responseTimes).astype(numpy.float)
    ackTimesMS = numpy.array(ackTimesMS).astype(numpy.float)
    numAcksReceivedInRequest = numpy.array(numAckIDsInRequest).astype(numpy.float)
    numAckIDsInRequest = numpy.array(numAckIDsInRequest).astype(numpy.float)
    numAcksReceivedWhenAtLeastOneReceived = numpy.array(numAcksReceivedWhenAtLeastOneReceived).astype(numpy.float)

    print "RESULTS:\n"

    # number of requests
    print("\n********* Number of requests *********\n")

    print "Total number of event batches posted: "
    print "\t" + str(eventPosts)

    print "Total number of ack polls: "
    print "\t" + str(ackPolls)

    print "Total number of empty event posts: "
    print "\t" + str(emptyEventChecks)

    print "Total number of requests to /health: "
    print "\t" + str(healthEndpointChecks)

    print "Total number of 'ack checks': "
    print "\t" + str(ackChecks)

    print "Total requests: "
    print "\t" + str(eventPosts + ackPolls + emptyEventChecks + healthEndpointChecks + ackChecks)

    # response times

    print("\n********* Response times *********\n")

    print "Average response time: "
    print "\t" + str(numpy.mean(responseTimes))

    print "Standard deviation of response times: "
    print "\t" + str(numpy.std(responseTimes))

    # back pressure and channel health
    print("\n********* Back pressure and channel availability *********\n")

    print "Total number of spins in load balancer: "
    print "\t" + str(lbSpins)

    print "Total number of 503 responses from event posts: "
    print "\t" + str(eventPostServerBusy)

    print "Total number of 503 responses from ack polls: "
    print "\t" + str(ackPollServerBusy)

    print "Total number of 503 responses from HttpCallbacksGeneric: "
    print "\t" + str(genericServerBusy)

    print "Total number of times a channel became unhealthy: "
    print "\t" + str(channelBecameUnavailable)

    print "Total number of times a channel became healthy: "
    print "\t" + str(channelBecameAvailable)

    # ack metrics
    print("\n********* Ack Metrics *********\n")

    print "Total number of acknowledged batches: "
    print "\t" + str(len(ackTimesMS))

    print "Megabytes acknowledged (assuming 5MB batches)"
    print "\t" + str(len(ackTimesMS) * 5)

    print "Average ack time for an event batch: "
    print "\t" + str(numpy.mean(ackTimesMS))

    print "Standard deviation of ack times for an event batch: "
    print "\t" + str(numpy.std(ackTimesMS))

    print "Average number of acks received in ack poll response: "
    print "\t" + str(numpy.mean(numAcksReceivedInRequest))

    print "Average number of ackIDs sent in an ack poll request: "
    print "\t" + str(numpy.mean(numAckIDsInRequest))

    print "Average number of acks received in ack poll response when we get at least one: "
    print "\t" + str(numpy.mean(numAcksReceivedWhenAtLeastOneReceived))

    print("\n********* Sticky sessions violations *********\n")

    # sticky session
    print "Total number of session cookie violations detected: "
    print "\t" + str(cookieViolations)

    file.close()


def main(args, loglevel):
  logging.basicConfig(format="%(levelname)s: %(message)s", level=loglevel)
  logging.info("Reminder: make sure cloudfwd printed DEBUG log lines.")

  computeMetrics(args.filename)
 
# boilerplate
if __name__ == '__main__':
  parser = argparse.ArgumentParser( 
                                    description = "Does a thing to some stuff.",
                                    epilog = "As an alternative to the commandline, params can be placed in a file, one per line, and specified on the commandline like '%(prog)s @params.conf'.",
                                    fromfile_prefix_chars = '@' )

  parser.add_argument(
                      "filename",
                      help = "pass log file name to process",
                      metavar = "FILENAME")
  parser.add_argument(
                      "-v",
                      "--verbose",
                      help="increase output verbosity",
                      action="store_true")
  args = parser.parse_args()
  
  # Setup logging
  if args.verbose:
    loglevel = logging.DEBUG
  else:
    loglevel = logging.INFO
  
  main(args, loglevel)