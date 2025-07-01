import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import MainLayout from './layout/MainLayout';

const App: React.FC = () => {
    return (
        <BrowserRouter>
            <MainLayout />
        </BrowserRouter>
    );
};

export default App;
