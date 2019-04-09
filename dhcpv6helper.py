#!/usr/local/bin/python3

import netifaces
import ipaddress
import argparse
import configparser
import sys

parser = argparse.ArgumentParser(description='Helper for DHCPv6 Prefix Delegation')

parser.add_argument('-i', '--interface', nargs=1, help='Interface with prefix delegaton', required=True)
parser.add_argument('-t', '--template', nargs=1, help='Jinja2 template to populate', required=True)
parser.add_argument('-c', '--config', nargs=1, help='Optional configuration file. Command line args override config file.')
parser.add_argument('-p', '--prefix', nargs=1, help='Prefix length of subnets to be created, default=64', type=int)
parser.add_argument('-L', '--lowoffset', nargs=1, help='Number of prefixes to leave unallocated at the low end, default=0', type=int)
parser.add_argument('-H', '--highoffset', nargs=1, help='Number of prefixes to leave unallocated at the top end, default=0', type=int)
args = parser.parse_args()

#Argument defaults
length=64
low=0
top=0
interface=""
template=""


#Apply command-line arguments
if args.prefix != None:
    length=int(args.prefix[0])
if args.lowoffset != None:
    low=int(args.lowoffset[0])
if args.highoffset != None:
    top=int(args.highoffset[0])
if args.interface != None:
    interface=args.interface[0]
if args.template != None:
    template=args.template[0]

#Get all addresses from interface
alladdrs = netifaces.ifaddresses(interface)

#Extract only IPv6 addresses
addrs=alladdrs[netifaces.AF_INET6]

#Ignore non-global addresses
#There may be more than one global address, so we
#choose the largest subnet (smallest prefix number)

#Create an impossible subnet to compare sizes to
thisnet=('::', 129)

#Loop through addresses
for addrset in addrs:
    #Get address from netifaces object
    addr=addrset['addr']

    #Ignore non-global addresses
    network=ipaddress.IPv6Address(addr)
    if not network.is_global:
        continue

    #Extract just the prefix from the netifaces object
    prefix=addrset['netmask'].split('/')[1]
    prefixint=int(prefix)

    #Is this the largest subnet (smallest prefix number) so far?
    if prefixint < int(thisnet[1]):
        thisnet=(addr, prefix)
    #Loop again

print(thisnet)

#Number of subnets being created
prefixdiff=length-int(thisnet[1])
totalprefix=2**prefixdiff

#Size of each subnet
netsize=2**length

#IPv6Interface object for the address of the interface
#containing the delegated subnet
thisint=ipaddress.IPv6Interface('/'.join(thisnet))

#Get the network address of the interface
#This returns an IPv6Network object
netobj=thisint.network

#Get the actual address from the IPv6Network object
#This is the network of the whole delegation
thisnet=netobj.network_address
delegation=ipaddress.IPv6Address(thisnet)
print (delegation)

#Lowest address in range
lowrange=delegation + (netsize*low)

#Highest address in range
lastaddr=delegation+(netsize*totalprefix)
highrange=lastaddr-(netsize*top)
print (lowrange, highrange)
iscstring="""
subnet6 %s/%s {
  prefix6 %s %s /%s;
}
""" % (netobj.network_address, netobj.prefixlen, lowrange, highrange, length)

print (iscstring.strip())

#prefixdiff=args.length[0] - int(thisnet[1])
#maxnets=2**prefixdiff
#netnumber=1
#if args.number != None:
#    netnumber=args.number[0]
#if netnumber > maxnets:
#    print ("Only", maxnets, "are available", netnumber, "is invalid. Exiting",
#           file=sys.stderr)
#    sys.exit()
#netnumber = netnumber-1
#thisint=ipaddress.IPv6Interface('/'.join(thisnet))
#delegation=ipaddress.IPv6Network(thisint.network)
#subnets=list(delegation.subnets(new_prefix=args.length[0]))
#subnet=subnets[netnumber]
#prefix=subnet.prefixlen
#iplow=ipaddress.IPv6Address(subnet.network_address)+2
