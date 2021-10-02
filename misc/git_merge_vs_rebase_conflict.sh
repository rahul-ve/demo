#! /usr/bin/env bash


mkdir rebaseVSmerge
cd rebaseVSmerge/
git init
echo 'This is on master branch' > somefile.txt
git add .
git commit -am "added some code"
git switch -c branchA
echo 'This is on feature branch' > somefile.txt
git commit -am "overwrote some code"
git switch -
sed -i -e 's/This is on master branch/This is on master branch and I dont want this line modified by anyone!/' somefile.txt
git commit -am "add more code"
git switch -
git merge master            # this will throw a conflict
echo -e '\n ***NOTE THE CONFLICT***\n' && cat somefile.txt && echo -e '\n'
git merge --abort
git rebase master              # this will also throw a conflit but compare the conflict with above!
echo -e '\n ***NOTE THE CONFLICT***\n' && cat somefile.txt && echo -e '\n'
cd ..
# rm -rf rebaseVSmerge              # run this to clean up
