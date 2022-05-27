#!/bin/bash

cd "$( dirname -- "$0"; )"
cd .program
source venv/bin/activate

echo "|==========================|"
echo "| Enter the filename       |"
read filename
echo "| $filename is beeing      |"
echo "| transcribed              |"
echo "|==========================|"

python main.py ../$filename

cd model-punct
python example.py ../temp.txt
cd ..
rm audio.wav
rm temp.txt
echo "| Check result.txt!        |"
