# Personal Finance Management System

A comprehensive personal finance management system built with Python, featuring double-entry bookkeeping, automated transaction categorization, and tax form filling capabilities.

## Features

- **Double-Entry Bookkeeping**: Uses Beancount format for accurate financial tracking
- **Automated CSV Import**: Import transactions from various banks with intelligent categorization
- **LLM Integration**: Local Hermes LLM for transaction narration and categorization
- **Analytics Dashboard**: Fast analytics using DuckDB for financial insights
- **Form Filling**: Automated PDF form filling (IRS forms, etc.)
- **REST API**: FastAPI-based API for all operations
- **Data Normalization**: Clean and standardize transaction data

## Architecture

```
personal-finance/
├── api/              # FastAPI endpoints
├── analytics/        # DuckDB analytics and queries
├── ledger/           # Beancount ledger and import rules
├── llm/              # Local LLM client and prompts
├── forms/            # PDF form filling and validation
├── ingest/           # CSV import and normalization
├── storage/          # DuckDB database management
└── data/             # Sample data and templates
```

## Quick Start

### Development Mode

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start Hermes3 LLM Server** (in a separate terminal)
   ```bash
   ./run_hermes3.sh
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings (LLM URL should match run_hermes3.sh output)
   ```

4. **Initialize Database**
   ```bash
   python -m storage.duck
   ```

5. **Start API Server**
   ```bash
   python -m api.main
   ```

6. **Import Transactions**
   ```bash
   curl -X POST "http://localhost:8000/ingest/csv" \
        -F "file=@your_bank_export.csv" \
        -F "bank=chase"
   ```

7. **Stop LLM Server** (when done)
   ```bash
   ./stop_hermes3.sh
   ```

### Production Mode (Single Server)

For production, FastAPI serves both the API and the built frontend UI:

1. **Build Frontend** (if you have one)
   ```bash
   cd frontend && npm run build
   ```

2. **Start Production Server**
   ```bash
   ./start_production.sh
   ```

   Or manually:
   ```bash
   export ENVIRONMENT=production
   cd personal-finance
   python -m api.main
   ```

3. **Access Application**
   - API: `http://localhost:8000/docs`
   - Frontend: `http://localhost:8000/` (if built)

### Docker Deployment

**Production with Docker Compose:**
```bash
# Build and start services
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**Development with Docker:**
```bash
docker-compose -f docker-compose.dev.yml up --build
```

## Key Components

### Transaction Import & Normalization

- **CSV Parser**: Configurable parsers for different bank formats
- **Data Normalizer**: Clean dates, amounts, merchant names
- **Rule Engine**: YAML-based categorization rules
- **Beancount Integration**: Convert to double-entry format

### Analytics Engine

- **DuckDB Backend**: Fast analytical queries on transaction data
- **Parameterized Queries**: Safe, reusable SQL templates
- **Pre-built Analytics**: Cash flow, spending patterns, budgets
- **Custom Dashboards**: Build your own financial insights

### LLM Integration

- **Local Hermes Client**: Connect to llama.cpp server
- **Smart Categorization**: AI-powered transaction categorization
- **Natural Language**: Generate readable transaction descriptions
- **Privacy-First**: All processing happens locally

### Form Automation

- **PDF Form Filling**: Support for IRS and other tax forms
- **Field Mapping**: YAML-based field mapping configurations
- **Data Validation**: Ensure form accuracy and completeness
- **Multiple Formats**: AcroForm and overlay methods

## Configuration

### Bank Import Rules (`ledger/import_rules.yaml`)

```yaml
banks:
  chase:
    csv_format:
      date_column: "Transaction Date"
      amount_column: "Amount"
      description_column: "Description"
    category_rules:
      - pattern: "(?i)(grocery|supermarket)"
        category: "Expenses:Food:Groceries"
```

### Form Mappings (`forms/mappings/form_433a.yaml`)

```yaml
personal_info:
  taxpayer_name:
    field_name: "taxpayer_name"
    data_path: "taxpayer.full_name"
    required: true
```

## API Usage

### Import CSV Transactions
```bash
POST /ingest/csv
Content-Type: multipart/form-data

file: bank_export.csv
bank: chase
```

### Query Transactions
```bash
POST /query/transactions
Content-Type: application/json

{
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "category": "Food"
}
```

### Get Financial Summary
```bash
GET /analytics/summary?start_date=2024-01-01&end_date=2024-12-31
```

### Fill Tax Form
```bash
POST /forms/fill
Content-Type: application/json

{
  "form_type": "form_433a",
  "data": {
    "taxpayer": {"full_name": "John Doe"},
    "income": {"gross_monthly_wages": 5000}
  }
}
```

## Data Flow

1. **Import**: CSV files → Normalized transactions → Beancount entries
2. **Storage**: Beancount entries → DuckDB analytical tables
3. **Analytics**: DuckDB queries → Financial insights and reports
4. **Forms**: DuckDB data → PDF form filling → Completed documents

## Development

### Adding New Bank Support

1. Add bank configuration to `ledger/import_rules.yaml`
2. Define CSV format and categorization rules
3. Test with sample CSV files

### Adding New Forms

1. Create mapping YAML in `forms/mappings/`
2. Define field locations and validation rules
3. Test form filling with sample data

### Custom Analytics

1. Add SQL queries to `analytics/queries.sql`
2. Create wrapper functions in `analytics/analytics.py`
3. Expose via API endpoints in `api/main.py`

## Security Considerations

- **Local Processing**: All LLM processing happens locally
- **Data Privacy**: No financial data sent to external services
- **Access Control**: API authentication and authorization
- **Data Encryption**: Sensitive data encryption at rest

## Performance

- **DuckDB**: Columnar storage for fast analytics
- **Batch Processing**: Efficient bulk transaction imports
- **Caching**: Query result caching for common operations
- **Indexing**: Optimized database indexes for fast queries

## Backup and Recovery

- **Database Backups**: Automated DuckDB backups
- **Ledger Files**: Version control for Beancount files
- **Configuration**: Backup import rules and mappings
- **Data Export**: Export data in multiple formats

## Troubleshooting

### Common Issues

1. **CSV Import Failures**: Check bank configuration in import rules
2. **LLM Connection**: 
   - Verify Hermes server is running: `curl http://127.0.0.1:11434/health`
   - Check server logs: `tail -f /tmp/llm_server.log`
   - Restart server: `./stop_hermes3.sh && ./run_hermes3.sh`
3. **Form Filling**: Ensure PDF template and mappings are correct
4. **Database Errors**: Check DuckDB file permissions and disk space

### Logging

```bash
# View application logs
tail -f logs/finance.log

# Debug CSV import
python -c "from ingest.csv_to_ledger import CSVToLedgerConverter; CSVToLedgerConverter().convert(open('sample.csv').read(), 'chase')"
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.