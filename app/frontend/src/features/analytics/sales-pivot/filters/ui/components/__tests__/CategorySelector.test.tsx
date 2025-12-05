import { describe, it, expect, vi } from 'vitest';
import { CategorySelector } from '../CategorySelector';

describe('CategorySelector', () => {
  it.skip('廃棄物が選択された状態で表示される', () => {
    const onChange = vi.fn();
    // render(<CategorySelector value="waste" onChange={onChange} />);
    
    // const wasteButton = screen.getByText('廃棄物');
    // expect(wasteButton).toBeInTheDocument();
  });

  it.skip('有価物が選択された状態で表示される', () => {
    const onChange = vi.fn();
    // render(<CategorySelector value="valuable" onChange={onChange} />);
    
    // const valuableButton = screen.getByText('有価物');
    // expect(valuableButton).toBeInTheDocument();
  });

  it.skip('ボタンクリック時にonChangeが呼ばれる', async () => {
    // const user = userEvent.setup();
    const onChange = vi.fn();
    // render(<CategorySelector value="waste" onChange={onChange} />);
    
    // const valuableButton = screen.getByText('有価物');
    // await user.click(valuableButton);
    
    // expect(onChange).toHaveBeenCalledWith('valuable');
  });

  it.skip('両方のボタンが表示される', () => {
    const onChange = vi.fn();
    // render(<CategorySelector value="waste" onChange={onChange} />);
    
    // expect(screen.getByText('廃棄物')).toBeInTheDocument();
    // expect(screen.getByText('有価物')).toBeInTheDocument();
  });
});
