import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ModeSelector } from '../ModeSelector';

describe('ModeSelector', () => {
  it('顧客モードが選択された状態で表示される', () => {
    const onChange = vi.fn();
    render(<ModeSelector value="customer" onChange={onChange} />);

    expect(screen.getByText('顧客')).toBeInTheDocument();
    expect(screen.getByText('品名')).toBeInTheDocument();
    expect(screen.getByText('日付')).toBeInTheDocument();
  });

  it('品名モードが選択された状態で表示される', () => {
    const onChange = vi.fn();
    render(<ModeSelector value="item" onChange={onChange} />);

    expect(screen.getByText('品名')).toBeInTheDocument();
  });

  it('日付モードが選択された状態で表示される', () => {
    const onChange = vi.fn();
    render(<ModeSelector value="date" onChange={onChange} />);

    expect(screen.getByText('日付')).toBeInTheDocument();
  });

  it('モード変更時にonChangeが呼ばれる', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<ModeSelector value="customer" onChange={onChange} />);

    const itemButton = screen.getByText('品名');
    await user.click(itemButton);

    expect(onChange).toHaveBeenCalledWith('item');
  });

  it('すべてのモードオプションが表示される', () => {
    const onChange = vi.fn();
    render(<ModeSelector value="customer" onChange={onChange} />);

    expect(screen.getByText('顧客')).toBeInTheDocument();
    expect(screen.getByText('品名')).toBeInTheDocument();
    expect(screen.getByText('日付')).toBeInTheDocument();
  });
});
