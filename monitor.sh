#!/bin/bash
# set path to watch
DIR="/mnt/backup"
#DIR="/home/io"
# set path to copy the script to
target_dir="/web/tg"

while true
do

for f in $(find $DIR -name '*.mov' -or -name '*.MOV'  ); do
   length=${#DIR}+1
   to=${f:$length}
   echo $to
   to="$target_dir/$to"
  echo $to
    if test ! -f $to;then
	   echo "target not found"
	   basepath=$(dirname "$to")
           echo $basepath

           mkdir -p $basepath
           ffmpeg -i  "$f" -vcodec libx264  "$to" -y
    else
	   echo "target found"
    fi 
done
sleep 5
done

exit 0


#inotifywait -m -r -e moved_to -e close_write   "$DIR" --format "%w%f" | while read f
inotifywait -m -r -e create -e close  "$DIR" --format "%w%f"  | while read f
echo $f

do
    length=${#DIR}+1
    to=${f:$length}
    echo $to
    # check if the file is a .sh file
    if [[ $f = *.mov ]]; then
      # if so, copy the file to the target dir
      #mv "$DIR/$f" "$target_dir"
      to="$target_dir/$to"
      echo $to
      basepath=$(dirname "$to")
      echo $basepath

      mkdir -p $basepath
      ffmpeg -i  "$f" -vcodec libx264  "$to" -y
    fi
    sleep 3
done
