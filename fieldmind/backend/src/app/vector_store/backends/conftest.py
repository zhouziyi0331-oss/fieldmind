"""
pytest 配置文件
"""
import warnings

# 在所有测试之前禁用警告
def pytest_configure(config):
    warnings.filterwarnings("ignore")
