## Step 1
Put the latest version of the chromedriver in the chromedriver/ folder as __chromedriver_linux.zip__ if using linux or __chromedriver_mac.zip__ if using mac. 

## Step 2
Put all websites in the file __urllist.csv__. The first column should have the names of the websites. The website is saved under __html/name/__.

## Step 3
Run __splitter.py__. It splits the total number of websites into a group of 5, and creates separate folders for each. This is to make it easier to keep track of the download in cases of large number of websites. Each group of 5 is contained within its own __part__ folder. 

## Step 4
Run __runner.sh__. It runs the crawler one at a time by going into each __part__ folder, until all the parts are complete. 

