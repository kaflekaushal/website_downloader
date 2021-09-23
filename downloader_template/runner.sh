for partfolder in part*;
do 
cd $partfolder
echo "working on $partfolder"
python3 crawler.py
cd ..
done

