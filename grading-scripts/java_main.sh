#!/bin/bash

cd "$( dirname "${BASH_SOURCE[0]}" )" && javac *.java && timeout --kill-after=15 java Main
