#!/bin/bash

cd ..

#reload templates
. env/bin/activate
python app_tt/pb_apps/tt_apps/ttapps.py -u caracterizaoeten2001bras_tt1
python app_tt/pb_apps/tt_apps/ttapps.py -u caracterizaoeten2001bras_tt2
python app_tt/pb_apps/tt_apps/ttapps.py -u caracterizaoeten2001bras_tt3
deactivate


sudo service rabbitmq-server restart
sudo service supervisor stop
sudo service supervisor start
sudo service apache2 restart

#reload templates
#. env/bin/activate
#python app_tt/pb_apps/tt_apps/ttapps.py -u caracterizaoeten2001bras_tt1
#python app_tt/pb_apps/tt_apps/ttapps.py -u caracterizaoeten2001bras_tt2
#python app_tt/pb_apps/tt_apps/ttapps.py -u caracterizaoeten2001bras_tt3
#deactivate