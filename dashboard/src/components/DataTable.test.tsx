import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect } from 'vitest';
import { DataTable } from './DataTable';
import type { Column } from './DataTable';

interface Item {
  id: number;
  name: string;
  score: number;
}

const columns: Column<Item>[] = [
  { key: 'name', header: 'Name', sortable: true },
  { key: 'score', header: 'Score', sortable: true },
];

const data: Item[] = [
  { id: 1, name: 'Alice', score: 90 },
  { id: 2, name: 'Bob', score: 75 },
  { id: 3, name: 'Charlie', score: 85 },
];

describe('DataTable', () => {
  it('renders all rows', () => {
    render(<DataTable columns={columns} data={data} keyExtractor={(i) => i.id} />);
    expect(screen.getByText('Alice')).toBeInTheDocument();
    expect(screen.getByText('Bob')).toBeInTheDocument();
    expect(screen.getByText('Charlie')).toBeInTheDocument();
  });

  it('renders column headers', () => {
    render(<DataTable columns={columns} data={data} keyExtractor={(i) => i.id} />);
    expect(screen.getByText('Name')).toBeInTheDocument();
    expect(screen.getByText('Score')).toBeInTheDocument();
  });

  it('shows empty message when no data', () => {
    render(
      <DataTable columns={columns} data={[]} keyExtractor={(i: Item) => i.id} emptyMessage="No items" />,
    );
    expect(screen.getByText('No items')).toBeInTheDocument();
  });

  it('sorts by column when clicked', async () => {
    const user = userEvent.setup();
    render(<DataTable columns={columns} data={data} keyExtractor={(i) => i.id} />);

    // Click Score header to sort ascending
    await user.click(screen.getByText('Score'));

    const rows = screen.getAllByRole('row');
    // Header row + 3 data rows
    expect(rows).toHaveLength(4);
    // First data row should be Bob (75) after ascending sort
    expect(rows[1]).toHaveTextContent('Bob');
  });

  it('toggles sort direction on second click', async () => {
    const user = userEvent.setup();
    render(<DataTable columns={columns} data={data} keyExtractor={(i) => i.id} />);

    const header = screen.getByText('Score');
    await user.click(header); // ascending
    await user.click(header); // descending

    const rows = screen.getAllByRole('row');
    // First data row should be Alice (90) after descending sort
    expect(rows[1]).toHaveTextContent('Alice');
  });

  it('uses custom render function', () => {
    const customColumns: Column<Item>[] = [
      { key: 'name', header: 'Name', render: (item) => <strong>{item.name}!</strong> },
    ];
    render(<DataTable columns={customColumns} data={data} keyExtractor={(i) => i.id} />);
    expect(screen.getByText('Alice!')).toBeInTheDocument();
  });
});
