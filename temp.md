# Giải bài toán Linear Regression
## Trình bày bài toán
Bài toán Linear Regression (hồi quy tuyến tính) là một kỹ thuật thống kê được sử dụng để mô hình hóa *mối quan hệ giữa một biến phụ thuộc (biến mục tiêu) và một hoặc nhiều biến độc lập (biến giải thích)*. Mục tiêu của bài toán là tìm ra một hàm tuyến tính sao cho giá trị dự đoán từ hàm này gần nhất với giá trị thực tế của biến phụ thuộc.
Công thức tổng quát của mô hình Linear Regression có dạng:
$$
y = \beta_0 + \beta_1 x_1 + \beta_2 x_2 + \ldots + \beta_p x_p + \epsilon
$$
Trong đó:
- $y$ là biến phụ thuộc (giá trị mục tiêu).
- $x_1, x_2, \ldots, x_p$ là các
    biến độc lập (đặc trưng).
- $\beta_0$ là hệ số chặn (intercept).
- $\beta_1, \beta_2, \ldots, \beta_p$ là các hệ số hồi quy (coefficients) tương ứng với các biến độc lập.
- $\epsilon$ là sai số ngẫu nhiên (error term).

## Hàm mất mát Mean Squared Error (MSE)
Hàm mất mát Mean Squared Error (MSE) được sử dụng phổ biến trong các bài toán hồi quy để đo lường sự khác biệt giữa giá trị dự đoán và giá trị thực tế. Công thức của MSE được định nghĩa như sau:
$$
MSE = \frac{1}{n} \sum_{i=1}^{n} (y_i - (\beta_0 + \beta_1 x_{i1} + \beta_2 x_{i2} + \ldots + \beta_p x_{ip}))^2 = \frac{1}{n} \sum_{i=1}^{n} (y_i - \hat{y}_i)^2
$$
Trong đó:
- $n$ là số lượng mẫu dữ liệu.
- $y_i$ là giá trị thực tế của mẫu thứ $i$.
- $\hat{y}_i$ là giá trị dự đoán của mẫu thứ $i$.
Hay được viết lại dưới dạng ma trận:
$$
MSE = \frac{1}{n} \sum_{i=1}^{n} (y_i- \mathbf{x}_i^T \boldsymbol{\beta})^2 = \frac{1}{n} (\mathbf{y} - \hat{\mathbf{y}})^T (\mathbf{y} - \hat{\mathbf{y}})
$$
Trong đó:
- $\mathbf{x}_i$ là vector đặc trưng của mẫu thứ $i$.
- $\boldsymbol{\beta}$ là vector các hệ số hồi quy.
- $\mathbf{y}$ là vector giá trị thực tế.
- $\hat{\mathbf{y}}$ là vector giá trị dự đoán.

## Giải bài toán Linear Regression sử dụng MSE
Để giải bài toán Linear Regression bằng cách tối thiểu hóa hàm mất mát MSE, ta có thể sử dụng phương pháp bình phương tối thiểu (Ordinary Least Squares - OLS). Mục tiêu là tìm vector hệ số $\boldsymbol{\beta}$ sao cho MSE được giảm thiểu.
Điều này xảy ra khi đạo hàm của MSE theo $\boldsymbol{\beta}$ bằng 0:
$$
\frac{\partial MSE}{\partial \boldsymbol{\beta}} = -\frac{2}{n} \mathbf{X}^T (\mathbf{y} - \mathbf{X} \boldsymbol{\beta}) = 0
$$
Giải phương trình trên ta được:
$$
\mathbf{X}^T \mathbf{y} = \mathbf{X}^
T \mathbf{X} \boldsymbol{\beta}
$$
Từ đó, ta có thể tìm được vector hệ số $\boldsymbol{\beta}$ như
sau:
$$
\boldsymbol{\beta} = (\mathbf{X}^T \mathbf{X})^{-1} \mathbf{X}^T \mathbf{y}
$$
Nhưng cần lưu ý rằng ma trận $\mathbf{X}^T \mathbf{X}$ phải khả nghịch (invertible) để có thể tính được nghịch đảo. Tại đây, ta có thể sử dụng phương pháp giả nghịch đảo (Moore-Penrose Pseudoinverse) để giải quyết trường hợp ma trận không khả nghịch.
Trong python, ta có thể sử dụng thư viện NumPy để tính toán như sau:
import numpy as np
# Giả sử X là ma trận đặc trưng và y là vector giá trị mục tiêu
X = np.array([[...], [...], ...])  # Ma trận đặc trưng
y = np.array([...])  # Vector giá trị mục tiêu
# Tính toán hệ số hồi quy sử dụng giả nghịch đảo
beta = np.linalg.pinv(X) @ y
print("Hệ số hồi quy:", beta)

Trong đó, np.linalg.pinv(X) tính toán giả nghịch đảo của ma trận X, và phép nhân ma trận @ được sử dụng để nhân giả nghịch đảo với vector y để thu được vector hệ số hồi quy beta.
## Kết luận
Bài toán Linear Regression là một kỹ thuật quan trọng trong học máy và thống kê để mô hình mối quan hệ tuyến tính giữa các biến. Bằng cách sử dụng hàm mất mát Mean Squared Error (MSE) và phương pháp bình phương tối thiểu, ta có thể tìm ra các hệ số hồi quy để dự đoán giá trị mục tiêu một cách hiệu quả.