import pandas as pd

in_table1 = pd.read_csv('data/sales1.csv', sep=',')
in_table2 = pd.read_csv('data/sales2.csv', sep=',')

print(len(in_table1))
print(len(in_table2))

out_table = pd.concat([in_table1, in_table2], ignore_index=True)

print(len(out_table))

out_table = out_table.drop_duplicates()

print(len(out_table))

out_table.to_csv('data/sales_concat.csv', sep=',', index=False)