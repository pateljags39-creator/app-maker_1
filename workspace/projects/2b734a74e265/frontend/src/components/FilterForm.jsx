import React, { useState } from 'react';
import { Search, Loader2, Info } from 'lucide-react';

const SECTORS = [
  "Technology",
  "Healthcare",
  "Financials",
  "Energy",
  "Consumer Discretionary",
  "Consumer Staples",
  "Industrials",
  "Materials",
  "Utilities",
  "Real Estate",
  "Communication Services"
];

const MARKETS = [
  "US (NYSE/NASDAQ)",
  "Europe",
  "Asia Pacific",
  "Global"
];

export default function FilterForm({ onSubmit, isLoading }) {
  const [sector, setSector] = useState(SECTORS[0]);
  const [market, setMarket] = useState(MARKETS[0]);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({ sector, market });
  };

  return (
    <div className="card filter-card" data-testid="filter-form-container">
      <div className="card-header">
        <h2 className="card-title">Research Parameters</h2>
        <p className="card-subtitle">Select your target sector and market to discover top-rated analysts.</p>
      </div>
      
      <form onSubmit={handleSubmit} className="filter-form" data-testid="filter-form">
        <div className="form-grid">
          {/* Active Filters */}
          <div className="form-group">
            <label htmlFor="sector" className="form-label">Sector</label>
            <select
              id="sector"
              value={sector}
              onChange={(e) => setSector(e.target.value)}
              className="form-control"
              disabled={isLoading}
              data-testid="select-sector"
            >
              {SECTORS.map(s => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="market" className="form-label">Market</label>
            <select
              id="market"
              value={market}
              onChange={(e) => setMarket(e.target.value)}
              className="form-control"
              disabled={isLoading}
              data-testid="select-market"
            >
              {MARKETS.map(m => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          </div>

          {/* Disabled / MVP Limitations */}
          <div className="form-group disabled-group">
            <label htmlFor="subsector" className="form-label">
              Subsector / Theme
              <span className="badge-soon" title="Not available in MVP">MVP</span>
            </label>
            <input
              type="text"
              id="subsector"
              placeholder="e.g. AI, Genomics..."
              className="form-control"
              disabled
              data-testid="input-subsector"
            />
          </div>

          <div className="form-group disabled-group">
            <label htmlFor="assetType" className="form-label">
              Asset Type
              <span className="badge-soon" title="Not available in MVP">MVP</span>
            </label>
            <select id="assetType" className="form-control" disabled data-testid="select-asset-type">
              <option>Stocks & ETFs</option>
            </select>
          </div>

          <div className="form-group disabled-group">
            <label htmlFor="timeHorizon" className="form-label">
              Time Horizon
              <span className="badge-soon" title="Not available in MVP">MVP</span>
            </label>
            <select id="timeHorizon" className="form-control" disabled data-testid="select-time-horizon">
              <option>12 Months</option>
            </select>
          </div>
        </div>

        <div className="form-actions">
          <div className="info-text" data-testid="filter-info-text">
            <Info size={16} className="info-icon" />
            <span>Analysis runs against a curated universe of credible financial analysts.</span>
          </div>
          <button 
            type="submit" 
            className="btn btn-primary" 
            disabled={isLoading}
            data-testid="btn-submit-filters"
          >
            {isLoading ? (
              <>
                <Loader2 size={18} className="spin" />
                <span>Analyzing...</span>
              </>
            ) : (
              <>
                <Search size={18} />
                <span>Generate Report</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}