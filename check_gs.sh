for h in House01 House02 House03 House04 House05; do
    gs="/home/zyc/vgr_data_scenarios/$h/gas_simulations"
    if [ -d "$gs" ]; then
        echo "$h OK: $(ls $gs | wc -l) configs"
    else
        echo "$h MISSING gas_simulations"
    fi
done
