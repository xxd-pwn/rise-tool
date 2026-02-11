import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import time

from queryreduction import get_simplified_query
from utils.astoperation import myast2sql
from utils.common import read_from_tpcds
from utils.db import verify


if __name__ == '__main__':
    start_time = time.time()
    process_num = 0
    original_length = 0
    final_length = 0
    for i in range(1, 100):
        if i in [18]:
            continue
        print(f'Processing query {i}')
        sourcedb = 'PostgreSQL'
        targetdb = 'MySQL'
        sql = read_from_tpcds(i, 'TPC-DS-PostgreSQL')
        judge, info = verify(sourcedb, sql, targetdb, sql)
        if judge == True:
            print(f'Original SQL do not need new rules:\n{sql}')
        else:
            process_num  += 1
            original_length += len(sql)
            simplified_tree = get_simplified_query(sql, sourcedb, targetdb)
            simplified_sql = myast2sql(simplified_tree)
            final_length += len(simplified_sql)


            print(f'Simplified SQL from random delete:\n{simplified_sql}')
    end_time = time.time()
    print(f'Total time: {end_time - start_time}')
    print(f'Processed number of queries: {process_num}')
    print(f'Average time per query: {(end_time - start_time) / process_num}')
    print(f'Total length of original SQL: {original_length}')
    print(f'Total length of simplified SQL: {final_length}')
    print(f'Reduction ratio: {1 - final_length / original_length}')

