#! /usr/bin/env bash

# NOTE - this script will not work on Mac, depends on gnu tools like gnu-sed, coreutils, bash
# Install these via homebrew
# Install gnu tools and set the PATH in .bashrc to pick up gnu ones first
# refer to homebrew output for the PATH to set

mkdir rebaseVSmerge
cd rebaseVSmerge/
git init -b main

echo 'This is on main branch' > somefile.txt

git add .
git commit -am "added some code"

git switch -c feature

echo 'This is on feature branch' > somefile.txt
git commit -am "overwrote some code"

git switch -

sed -i -e 's/This is on main branch/This is on main branch and do not modify this line!/' somefile.txt
git commit -am "add more code"

git switch -

git merge main          # this will throw a conflict

echo -e '\n ***NOTE THE CONFLICT***\n' && cat somefile.txt && echo -e '\n'

git merge --abort

echo "Now try rebase instead, which will also throw the conflict but the context is flipped"

git rebase main              # this will also throw a conflit but compare the conflict with above!

echo -e '\n ***NOTE THE CONFLICT***\n' && cat somefile.txt && echo -e '\n'

git rebase --abort

# Uncomment below to cleanup
# cd ..
# rm -rf rebaseVSmerge              # run this to clean up
