function KnowledgeTable({ data, onSelect, selectedId }) {
  if (!data || data.length === 0) {
    return (
      <div className="knowledge-empty">
        <p>No topics found.</p>
      </div>
    );
  }

  return (
    <div className="knowledge-table-wrapper">
      <table className="knowledge-table">
        <thead>
          <tr>
            <th>Topic</th>
            <th>Category</th>
            <th>Subcategory</th>
            <th>Summary</th>
          </tr>
        </thead>

        <tbody>
          {data.map((item) => (
            <tr
              key={item.id}
              onClick={() => onSelect(item)}
              className={selectedId === item.id ? "selected-row" : ""}
            >
              <td>{item.title}</td>
              <td>{item.category}</td>
              <td>{item.subcategory}</td>
              <td>{item.summary}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default KnowledgeTable;