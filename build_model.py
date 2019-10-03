import xgboost as xgb

dtrain = xgb.DMatrix('data-clean.csv?format=csv&label_column=0')
dtest = xgb.DMatrix('data-clean.csv?format=csv&label_column=0')
param = {'max_depth': 2, 'eta': 1, 'objective': 'binary:logistic'}
param['nthread'] = 4
param['eval_metric'] = 'auc'

evallist = [(dtest, 'eval'), (dtrain, 'train')]

num_round = 10
bst = xgb.train(param, dtrain, num_round, evallist)
bst.save_model('0001.model')
