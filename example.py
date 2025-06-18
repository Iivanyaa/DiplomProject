import rollbar

rollbar.init(
  access_token='5f5889de2c144636b8936af63b2335ac',
  environment='testenv',
  code_version='1.0'
)
rollbar.report_message('Rollbar is configured correctly', 'info')