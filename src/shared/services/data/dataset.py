def collate_eeg_graphs(batch):
    """
    Custom collate: stack graphs trong một batch.
    Dùng thay cho DataLoader default collate.
    """
    from torch_geometric.data import Data, Batch

    data_list = []
    for x, edge_index, edge_weight, A in batch:
        data = Data(x=x, edge_index=edge_index, edge_attr=edge_weight, A=A)
        data_list.append(data)

    return Batch.from_data_list(data_list)