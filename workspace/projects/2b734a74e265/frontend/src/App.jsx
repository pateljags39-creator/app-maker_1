import React, { useState } from 'react';
import { LineChart, AlertCircle, Loader2, Search } from 'lucide-react';
import FilterForm from './components/FilterForm';
import ReportTabs from './components/ReportTabs';
import Disclaimers from './components/Disclaimers';
import { fetchReport } from './api';

function App() {
  const [reportData, setReportData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleFilterSubmit = async (filters) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchReport(filters);
      setReportData(data);
    } catch (err) {
      setError(err.message || 'An error occurred while fetching the analysis report.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="header-content">
          <div className="brand">
            <div className="brand-icon-wrapper">
              <LineChart className="brand-icon" size={24} />
            </div>
            <div>
              <h1 className="brand-title">Stock Analyst Analyzer</h1>
              <p className="brand-subtitle">Credibility-first financial research</p>
            </div>
          </div>
        </div>
      </header>

      <main className="main-content">
        <div className="layout-grid">
          <aside className="sidebar">
            <FilterForm onSubmit={handleFilterSubmit} isLoading={isLoading} />
          </aside>

          <section className="content-area">
            {isLoading && (
              <div className="state-container loading-state" data-testid="loading-state">
                <Loader2 className="spinner" size={40} />
                <h3>Analyzing Market Data</h3>
                <p>Evaluating analyst credibility and company solvency metrics...</p>
              </div>
            )}

            {error && !isLoading && (
              <div className="state-container error-state" data-testid="error-state">
                <AlertCircle size={40} className="error-icon" />
                <h3>Analysis Failed</h3>
                <p>{error}</p>
              </div>
            )}

            {!isLoading && !error && !reportData && (
              <div className="state-container empty-state" data-testid="empty-state">
                <div className="empty-icon-wrapper">
                  <Search size={32} />
                </div>
                <h3>No Data Generated Yet</h3>
                <p>Configure your sector and market preferences in the sidebar to discover top-rated analysts and their recommendations.</p>
              </div>
            )}

            {!isLoading && !error && reportData && (
              <div className="report-container" data-testid="report-container">
                <ReportTabs data={reportData} />
              </div>
            )}
          </section>
        </div>
      </main>

      <Disclaimers />
    </div>
  );
}

export default App;