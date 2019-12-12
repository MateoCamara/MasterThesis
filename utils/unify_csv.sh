metrica="_vifp.csv"
cd live_vifp

for i in *${metrica}*
do
	last_line="$(tail -n 1 $i)";
	valor_metrica=${last_line:(-9)}; # msssim = 8,`psnr = 9
	para_guardar=${i::-9}","$valor_metrica; # msssim = 11, psnr = 9
	echo $para_guardar >> resultados${metrica}_live;
done
mv resultados${metrica}_live ..
cd ..