# TrackShopSalesBot

This bot is already deployed and operational in Telegram Messenger under the handle [@TrackShopSalesBot](https://t.me/TrackShopSalesBot). In simple terms, this bot functions as a search engine for sales. It searches and tracks sales for your shop items (currently focused on groceries with available "letáky" or promotional flyers). For now, it works with a test PDF (used during development), but in the near future, I plan to upload new data.

## System Components

The main parts of the system are:
- **Admin Panel**
- **Data Pipeline**
- **Telegram Bot Update Handler**

All components interact with AWS services. Let’s dive into each part.

### Admin Panel

The admin panel is essentially a frontend + backend (React + Flask) website where I can upload PDF files and push them into the data pipeline. Here’s how it looks:

![Admin Panel Screenshot 1](https://drive.google.com/uc?export=view&id=1oC9DstJL4XCTvqCRt2hXypMp-Vfub1nY)
![Admin Panel Screenshot 2](https://drive.google.com/uc?export=view&id=16S2rurcbtPWzhc5DEytjUzhEEiNEFuuV)
![Admin Panel Screenshot 3](https://drive.google.com/uc?export=view&id=1FreXdkqI9qxZUoh6gJqj7vsuAzEQXArg)

On the backend, it interacts with the **DynamoDB `pdf_metadata` table**. The schema includes:

- `filename` (String)
- `shop_name` (String)
- `page_split` (Boolean)
- `s3_url` (String)
- `upload_date` (DateTime)
- `used` (Boolean)
- `valid_from` (Date)
- `valid_to` (Date)

Example data:

| filename                                         | shop_name        | page_split | s3_url                                                                                   | upload_date           | used  | valid_from | valid_to   |
|--------------------------------------------------|------------------|------------|------------------------------------------------------------------------------------------|-----------------------|-------|------------|------------|
| 5a1b5f1d-2868-4328-adf6-928edbbcd0f7.pdf         | Albert Hypermarket | true       | [Link](https://salestelegrambot.s3.amazonaws.com/pdfs/5a1b5f1d-2868-4328-adf6-928edbbcd0f7.pdf) | 2024-10-07 10:09:49   | false | 2024-10-02 | 2024-10-08 |
| b3234c3b-0c02-43d0-b86f-91c5a77fd111-1.pdf       | Albert Supermarket | false      | [Link](https://salestelegrambot.s3.amazonaws.com/pdfs/b3234c3b-0c02-43d0-b86f-91c5a77fd111-1.pdf) | 2024-10-09 16:10:27   | false | 2024-10-02 | 2024-10-08 |
| b3234c3b-0c02-43d0-b86f-91c5a77fd111.pdf         | Albert Supermarket | true       | [Link](https://salestelegrambot.s3.amazonaws.com/pdfs/b3234c3b-0c02-43d0-b86f-91c5a77fd111.pdf) | 2024-10-07 10:07:31   | false | 2024-10-02 | 2024-10-08 |

The admin panel visually highlights in **red** when PDF files are soon to be invalid. It also provides a page for uploading files and a "push to pipeline" button.

### Data Pipeline

The next important component is the **data pipeline**. Information and code about it can be found in a separate repository:

_Include repository link here..._

### Telegram Bot

Now, let's talk about the **Telegram Bot**. Here's the initial flow diagram of how the bot works:

_Include diagram here..._

The bot is currently available as an AWS Lambda function.

