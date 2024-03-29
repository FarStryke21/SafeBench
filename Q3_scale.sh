python scripts/run.py --mode=eval --agent_cfg faster_rcnn.yaml --scenario_cfg object_detection_stopsign.yaml --patch 'stopsign_q3_scale50' --exp_name scale_50_frcnn --num_scenario 4
python scripts/run.py --mode=eval --agent_cfg faster_rcnn.yaml --scenario_cfg object_detection_stopsign.yaml --patch 'stopsign_q3_scale100' --exp_name scale_100_frcnn --num_scenario 4 
python scripts/run.py --mode=eval --agent_cfg faster_rcnn.yaml --scenario_cfg object_detection_stopsign.yaml --patch 'stopsign_q3_scale150' --exp_name scale_150_frcnn --num_scenario 4
python scripts/run.py --mode=eval --agent_cfg faster_rcnn.yaml --scenario_cfg object_detection_stopsign.yaml --patch 'stopsign_q3_scale200' --exp_name scale_200_frcnn --num_scenario 4
python scripts/run.py --mode=eval --agent_cfg faster_rcnn.yaml --scenario_cfg object_detection_stopsign.yaml --patch 'stopsign_q3_scale250' --exp_name scale_250_frcnn --num_scenario 4
