import { describe, it, expect, vi } from 'vitest';
import { ModeSelector } from '../ModeSelector';

describe('ModeSelector', () => {
  it.skip('顧客モードが選択された状態で表示される', () => {
    const onChange = vi.fn();
    // render(<ModeSelector value="customer" onChange={onChange} />);
    
    // expect(screen.getByText('顧客')).toBeInTheDocument();
    // expect(screen.getByText('品名')).toBeInTheDocument();
    // expect(screen.getByText('日付')).toBeInTheDocument();
  });

  it.skip('品名モードが選択された状態で表示される', () => {
    const onChange = vi.fn();
    // render(<ModeSelector value="item" onChange={onChange} />);
    
    // expect(screen.getByText('品名')).toBeInTheDocument();
  });

  it.skip('日付モードが選択された状態で表示される', () => {
    const onChange = vi.fn();
    // render(<ModeSelector value="date" onChange={onChange} />);
    
    // expect(screen.getByText('日付')).toBeInTheDocument();
  });

  it.skip('モード変更時にonChangeが呼ばれる', async () => {
    // const user = userEvent.setup();
    const onChange = vi.fn();
    // render(<ModeSelector value="customer" onChange={onChange} />);
    
    // const itemButton = screen.getByText('品名');
    // await user.click(itemButton);
    
    // expect(onChange).toHaveBeenCalledWith('item');
  });

  it.skip('すべてのモードオプションが表示される', () => {
    const onChange = vi.fn();
    // render(<ModeSelector value="customer" onChange={onChange} />);
    
    // expect(screen.getByText('顧客')).toBeInTheDocument();
    // expect(screen.getByText('品名')).toBeInTheDocument();
    // expect(screen.getByText('日付')).toBeInTheDocument();
  });
});
