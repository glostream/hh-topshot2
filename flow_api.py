import grpc
import flow.access.access_pb2_grpc as access_pb2_grpc
import flow.access.access_pb2 as access_pb2
import pandas as pd
import json, time, os


MAIN_NODE = 'access.mainnet.nodes.onflow.org:9000'


def get_latest_block():
	channel = grpc.insecure_channel(MAIN_NODE)
	stub = access_pb2_grpc.AccessAPIStub(channel)
	response = stub.GetLatestBlock(access_pb2.GetLatestBlockRequest())
	latest_block_height = response.block.height

	return latest_block_height


def make_moments_purchased_request(stub, start, end):
	response = stub.GetEventsForHeightRange(access_pb2.GetEventsForHeightRangeRequest(
		type='A.c1e4f4f4c4257510.Market.MomentPurchased',
		start_height=start,
		end_height=end))

	return response.results


def make_moments_listed_request(stub, start, end):
	response = stub.GetEventsForHeightRange(access_pb2.GetEventsForHeightRangeRequest(
		type='A.c1e4f4f4c4257510.Market.MomentListed',
		start_height=start,
		end_height=end))

	return response.results


def make_moments_withdrawn_request(stub, start, end):
	response = stub.GetEventsForHeightRange(access_pb2.GetEventsForHeightRangeRequest(
		type='A.c1e4f4f4c4257510.Market.MomentWithdrawn',
		start_height=start,
		end_height=end))

	return response.results


def make_moments_price_changed_request(stub, start, end):
	response = stub.GetEventsForHeightRange(access_pb2.GetEventsForHeightRangeRequest(
		type='A.c1e4f4f4c4257510.Market.MomentPriceChanged',
		start_height=start,
		end_height=end))

	return response.results


def get_node(block, node_list):
	if block < node_list[0]['start']:
		raise Exception('block too old')

	for n in node_list:
		if n['start'] <= block <= n['end']:
			channel = grpc.insecure_channel(n['node'])
			stub = access_pb2_grpc.AccessAPIStub(channel)
			return n['node'], stub

	raise Exception('node not found for block {}'.format(block))


def build_node_list():
	channel = grpc.insecure_channel(MAIN_NODE)
	stub = access_pb2_grpc.AccessAPIStub(channel)
	response = stub.GetLatestBlock(access_pb2.GetLatestBlockRequest())
	latest_block_height = response.block.height

	## block 10523501 is Jan 1 2021 ~ 6AM GMT
	node_list = [{'node': 'access-001.mainnet4.nodes.onflow.org:9000', 'start': 9997081, 'end': 12020337}, # end 12020741
		{'node': 'access-001.mainnet5.nodes.onflow.org:9000', 'start': 12020337, 'end': 12609237},
		{'node': 'access-001.mainnet6.nodes.onflow.org:9000', 'start': 12609237, 'end': 13404176},
		{'node': MAIN_NODE, 'start': 13404176, 'end': latest_block_height}] # 13623980

	return node_list


def get_moments(request_function, start, end):
	latest_block_height = get_latest_block()
	node_list = build_node_list()

	results = []
	for batch_start in range(start, end, 249):
		batch_end = batch_start + 249

		if batch_end >= latest_block_height:
			batch_end = latest_block_height - 1

		print('getting events in range: {} -> {}'.format(batch_start, batch_end))

		node1, stub1 = get_node(batch_start, node_list)
		node2, stub2 = get_node(batch_end, node_list)

		if node2 == node1:
			response = request_function(stub1, batch_start, batch_end)
			for r in response:
				results.append(r)
		else:
			for bb in range(batch_start, batch_end):
				node, _ = get_node(bb, node_list)
				if node != node1:
					response = request_function(stub1, batch_start, bb)
					for r in response:
						results.append(r)
					response = request_function(stub2, bb, batch_end)
					for r in response:
						results.append(r)
					break

	return results


def parse_block(block, rows):
	current_block_height = block.block_height
	timestamp = block.block_timestamp.seconds
	for event in block.events:
		payload = json.loads(event.payload.decode())
		price = ''
		for f in payload['value']['fields']:
			if f['name'] == 'id':
				moment_id = f['value']['value']
			elif f['name'] == 'price':
				price = f['value']['value']
			elif f['name'] in ['seller', 'owner']:
				owner = f['value']['value']['value']
		row = {'Block Height': current_block_height, 'Timestamp': timestamp, 'Token ID': moment_id,
			'Owner': owner}
		if price:
			row['Price (USD)'] = price
		rows.append(row)
	
	return rows


def main():
	latest_block_height = get_latest_block()
	print('Latest block: {}'.format(latest_block_height))

	moments_listed = get_moments(make_moments_listed_request, latest_block_height - 500, latest_block_height)

	rows = []
	for block in moments_listed:
		rows = parse_block(block, rows)

	table = pd.DataFrame(rows)
	
	print(table)
	table.to_csv('./moments.csv', index=False)


if __name__ == '__main__':
	main()
