from question_bank import load_bank
bank, source = load_bank(force_refresh=True)
print(f'Loaded {len(bank)} questions from {source}.')
if len(bank) < 400:
    print('Full catalog was not downloaded. Check your internet connection and try again.')
