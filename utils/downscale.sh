for i in *; do cd $i; for j in *; do ffmpeg -i $j -vf scale=480:270 -sws_flags neighbor ../../"cuadros diferencia 270p"/$j; done; cd ..; mkdir ../"cuadros diferencia 270p"/$i; mv ../"cuadros diferencia 270p"/*jpg ../"cuadros diferencia 270p"/$i; done

