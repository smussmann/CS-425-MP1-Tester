#!/usr/bin/env python

#import argparse
import optparse
import collections
import multiprocessing
import os
import subprocess
import sys
import time

class dummy_obj:
  pass

def parse_file(f):
  commands = {'wait': 2, 'send': 2, 'crash': 1}
  output = []
  current = None
  for line in f.readlines():
    line = line.split(None, 2)
    if (line[0].startswith('[')):
      try:
        process_name = line[0][1:-1]
        current = (process_name, list())
        output.append(current)
      except:
        print "=> Name extraction failure"
        raise
    elif commands.has_key(line[0]):
      current[1].append(line)
    else:
      print "=> Unknown command %s with args %s" % tuple(line)
      sys.exit(1)

  return output

def run_cmds(command_list, name, pipe):
  commands = {'wait': lambda x: time.sleep(float(x)),
              'send': lambda x: p.stdin.write('%s\n' % x),
              'crash': lambda x: p.terminate()}
  pipe.recv()
  p = subprocess.Popen('./chat', stdin=subprocess.PIPE, stdout=subprocess.PIPE,
      stderr=subprocess.STDOUT)
  for command, arg in command_list:
    commands[command](arg)
  if p.poll() is not None:
    p.terminate()
  pipe.send(p.communicate()[0])
  pipe.close()

def main():
  #parser = argparse.ArgumentParser('Runs test instances of ./chat.')
  #parser.add_argument('infile', type=file)
  #parser.add_argument('-o', '--outfile', type=file, default=open('test.out.txt', 'w')
  #args = parser.parse_arguments()
  parser = optparse.OptionParser()
  parser.add_option('-o', '--outfile')
  options, o_args = parser.parse_args()

  args = dummy_obj()
  args.infile = open(o_args[0], 'r')
  if options.outfile == None:
    args.outfile = open('test.out.txt', 'w')
  else:
    args.outfile = open(options.outfile, 'w')

  commands = parse_file(args.infile)
  names = [x[0] for x in commands]

  processes = {}
  for name, cmds in commands:
    processes[name] = {}
    processes[name]['pipe'] = multiprocessing.Pipe()
    processes[name]['process'] = (multiprocessing.Process(target=run_cmds,
          args=(cmds, name, processes[name]['pipe'][1])))
    processes[name]['process'].start()

  # Start the processes
  for name in names:
    processes[name]['pipe'][0].send('start')
  # Wait for all processes to finish
  for name in names:
    processes[name]['process'].join()

  for name in names:
    args.outfile.write('=' * 8 + ' ' + name + ' ' + '=' * 8 + '\n')
    args.outfile.write(processes[name]['pipe'][0].recv())

  os.remove('GROUPLIST')

if __name__ == '__main__':
  main()
