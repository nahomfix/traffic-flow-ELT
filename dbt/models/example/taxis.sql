select * from {{ source('traffic_flow_dev', 'traffic_flow') }} where type = 'Taxi'
