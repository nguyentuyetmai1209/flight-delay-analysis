## Nguồn dữ liệu

### Dữ liệu chuyến bay chính

Dữ liệu chuyến bay được lấy từ BTS
(Reporting Carrier On-Time Performance) năm 2025.

Dữ liệu được tải theo từng tháng và lưu tại:

data/raw/bts/

Các thông tin chính bao gồm:
- ngày bay;
- hãng hàng không;
- sân bay đi;
- sân bay đến;
- giờ dự kiến;
- độ trễ khởi hành;
- độ trễ khi đến;
- tình trạng hủy/chuyển hướng;
- các nguyên nhân gây chậm chuyến.

### Dữ liệu tham chiếu

Hai file:

- `airlines.csv`
- `airports.csv`

được lấy từ bộ dữ liệu **2015 Flight Delays and Cancellations**
trên Kaggle.

`airlines.csv` được sử dụng để ánh xạ mã hãng
`IATA_CODE` sang tên hãng hàng không.

`airports.csv` được sử dụng để bổ sung tên sân bay,
thành phố, bang, quốc gia và tọa độ cho các mã
`Origin` và `Dest`.

Các file Kaggle chỉ đóng vai trò dữ liệu tham chiếu,
không phải dữ liệu chuyến bay chính của đề tài.