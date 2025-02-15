from airflow.models import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

import yfinance as yf
import pandas as pd

# Method to extract stock value from yahoo finaance library.

def extract_stock(symbol, location):
    start_date = datetime.today() - timedelta(days=1)
    end_date = start_date + timedelta(days=1)
    df = yf.download(symbol, start=start_date, end=end_date, interval='15m')
    print('after call yf.download', df.head())
    print(df.head)
    filename = f'{location}/{symbol}.csv'
    print('write to ', filename)
    df.to_csv(filename, header=False)


def query_stock(location):
    df = pd.read_csv(f'{location}/AAPL.csv')
    print('AAPL data:')
    print(df.head())

    df = pd.read_csv(f'{location}/TSLA.csv')
    print('TSLA data:')
    print(df.head())



# configure the flow to retry every 5 min for 2 attempts
default_args = {
    'start_date': datetime(2024, 8, 1),
    'schedule_interval': None,
    #'retries': 2,
    #'retry_delay': timedelta(minutes=55),
}
today_str = (datetime.now()).strftime('%Y-%m-%d')
#raw_data_loc = '/tmp/data/$(date "+%Y-%m-%d")'
raw_data_loc = f'/home/test/airflow/{today_str}'
extract_data_loc = '/home/test/airflow/extracted/'

#run the workflow on 6 PM every work day
dag = DAG(
    dag_id='marketvol',
    default_args=default_args,
    description='A simple DAG',
    #schedule_interval="* 18 * * 1,2,3,4,5"
    #schedule_interval = None

)

# create a temporary location
t0 = BashOperator(
    task_id='init_dir',
    bash_command=f'mkdir -p {raw_data_loc}',
    #bash_command=f'echo "Hello How are you"',
    dag=dag
)

#extract data for symbol AAPL
t1 = PythonOperator(
    task_id='extract_stock1',
    dag=dag,
    python_callable=extract_stock,
    op_kwargs={'symbol': 'AAPL', 'location': raw_data_loc}
)

#extract data for symbol TSLA
t2 = PythonOperator(
    task_id='extract_stock2',
    dag=dag,
    python_callable=extract_stock,
    op_kwargs={'symbol': 'TSLA', 'location': raw_data_loc}
)
# # move data download into a same place
t3 = BashOperator(
    task_id='move_data1',
    dag=dag,
    bash_command=f'mv {raw_data_loc}/AAPL.csv {extract_data_loc}'
)
t4 = BashOperator(
    task_id='move_data2',
    dag=dag,
    bash_command=f'mv {raw_data_loc}/TSLA.csv {extract_data_loc}'
)

# #extract data for symbol TSLA
t5 = PythonOperator(
    task_id='query_data',
    dag=dag,
    python_callable=query_stock,
    op_kwargs={'location': extract_data_loc}
)

t0 >> [t1, t2]
t1 >> t3
t2 >> t4
[t3, t4] >> t5