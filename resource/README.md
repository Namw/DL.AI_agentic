# resource ✅

**概述**

包含与示例数据相关的资源文件，用于项目中多个示例和可视化脚本。

**主要文件**

- `coffee_sales.csv` — 咖啡店销售示例数据，列包括：
  - date (M/D/YY)
  - time (HH:MM)
  - cash_type (card 或 cash)
  - card (string)
  - price (number)
  - coffee_name (string)
  - quarter (1-4)
  - month (1-12)
  - year (YYYY)

**使用场景**

- `reflection2_4/coffee_sales.py` 与 `coffee_salesv2.py` 使用该 CSV 做绘图与模型反思示例。
- 可在 Jupyter 或脚本中用 pandas 加载并预处理：
  ```python
  import pandas as pd
  df = pd.read_csv('resource/coffee_sales.csv')
  ```

**注意**

- 请在运行依赖 LLM 的脚本前确保已配置相应 API Key（详见根目录 README）。