# TrackShopSalesBot

This bot is already deployed and operational in Telegram Messenger under the handle [@TrackShopSalesBot](https://t.me/TrackShopSalesBot). Simply put, this bot functions as a search engine for sales. It tracks and searches for sales on shop items (currently focused on groceries with available "letáky" or promotional flyers). For now, it works with a test PDF (used during development), but soon I plan to upload new data.

<img src="https://drive.google.com/uc?export=view&id=18wwmwhRewnwtS2H4ENvcDE6fdqo-jpZK" width="250" height="500">

## System Components

The main parts of the system are:
- **Admin Panel**
- **Data Pipeline**
- **Telegram Bot Update Handler**

All components interact with AWS services. Let’s dive into each part.

### Admin Panel

The admin panel is a frontend + backend (React + Flask) website where I can upload PDF files and push them into the data pipeline. Here’s how it looks:

![Admin Panel Screenshot 1](https://drive.google.com/uc?export=view&id=1FreXdkqI9qxZUoh6gJqj7vsuAzEQXArg)
![Admin Panel Screenshot 2](https://drive.google.com/uc?export=view&id=16S2rurcbtPWzhc5DEytjUzhEEiNEFuuV)
![Admin Panel Screenshot 3](https://drive.google.com/uc?export=view&id=1oC9DstJL4XCTvqCRt2hXypMp-Vfub1nY)

The admin panel visually highlights in **red** when PDF files are about to expire. It also provides a page for uploading files and a "push to pipeline" button.

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

| filename                                         | shop_name         | page_split | s3_url                                                                                   | upload_date           | used  | valid_from | valid_to   |
|--------------------------------------------------|-------------------|------------|------------------------------------------------------------------------------------------|-----------------------|-------|------------|------------|
| 5a1b5f1d-2868-4328-adf6-928edbbcd0f7.pdf         | Albert Hypermarket | true       | [Link](https://salestelegrambot.s3.amazonaws.com/pdfs/5a1b5f1d-2868-4328-adf6-928edbbcd0f7.pdf) | 2024-10-07 10:09:49   | false | 2024-10-02 | 2024-10-08 |
| b3234c3b-0c02-43d0-b86f-91c5a77fd111-1.pdf       | Albert Supermarket | false      | [Link](https://salestelegrambot.s3.amazonaws.com/pdfs/b3234c3b-0c02-43d0-b86f-91c5a77fd111-1.pdf) | 2024-10-09 16:10:27   | false | 2024-10-02 | 2024-10-08 |
| b3234c3b-0c02-43d0-b86f-91c5a77fd111.pdf         | Albert Supermarket | true       | [Link](https://salestelegrambot.s3.amazonaws.com/pdfs/b3234c3b-0c02-43d0-b86f-91c5a77fd111.pdf) | 2024-10-07 10:07:31   | false | 2024-10-02 | 2024-10-08 |

Currently, the system is running locally. I plan to integrate a system using **Airflow** that will automatically check the validity of PDF files based on their expiration date. Additionally, I will develop a notification system using **AWS** to send email alerts when a leták is nearing expiration.

### Data Pipeline

The next important component is the **data pipeline**. Information and code for this component can be found in a separate repository:

[_Repository link here..._](https://github.com/Maniachenko/sales_telegram_bot_data_pipeline)

### Telegram Bot

Here’s the flow diagram showing how the **Telegram Bot** works:

![Diagramflow of Telegram Bot](https://drive.google.com/uc?export=view&id=1K54JPTAeJjDfWXRbZi1JUCRo8FgSWlwq)

The bot is currently deployed as an AWS Lambda function.

#### How the Bot Works

The bot interacts with users in Telegram Messenger, helping them track prices, manage sale sheets, and compare items across different shops. The system leverages AWS services like S3 for file storage, DynamoDB for storing user preferences and tracking data, and Lambda functions for real-time event handling. Below is a breakdown of how the bot operates:

1. **User Interaction Flow**
    - **Start Command (`/start`)**: The bot welcomes new users, guiding them through language selection and shop tracking setup. Returning users are taken directly to the main menu.

2. **Main Menu Options**
    - **🔍 Search for Item**: Users can search for specific items across shops, receiving item details including prices and images (if enabled).
    - **🛒 Add Shop Item to Track Price**: Users can add items to a tracking list. The bot monitors these items and notifies the user when they are on sale.
    - **🛍 Compare Shopping List Over Shops**: Users can compare prices of items across different shops by selecting shops and entering their shopping list.
    - **⚙️ Settings**: Allows users to manage preferences like excluding or including shops, toggling sale sheet PDF, enabling/disabling item photo groups, and adjusting language settings.
    - **ℹ️ About Project**: Provides information about the bot and its purpose.

3. **Settings Menu**
    - Users can exclude/include shops for tracking, manage their tracked items, toggle options like item photo groups, and change the interface language.

4. **Shop Selection and Item Tracking**
    - The bot ensures users include at least one shop for tracking. When an item is added to the tracking list, the bot monitors the item’s price and notifies the user when it goes on sale.

5. **Search and N-Gram Matching**
    - The bot uses n-gram matching to find items by searching for flexible name variations in the **DynamoDB `detected_data_table`**.

6. **Media Handling**
    - The bot can send item images in media groups (albums) through Telegram, allowing users to view products along with pricing information.

7. **State Management**
    - The bot saves user preferences and interaction states in **DynamoDB**, ensuring a seamless user experience across sessions.
        - **State Saving**: The bot saves the user’s current state (e.g., searching, tracking) to resume interaction seamlessly.
        - **Shop Selection History**: Maintains a history of selected shops, making it easy for users to reselect shops in the future.

8. **AWS S3 and DynamoDB Integration**
    - The bot downloads files from **S3** and processes item images and sale sheets. **DynamoDB** is used to store and retrieve user preferences, tracked items, shop selection history, and other related data.

#### How the Bot Works

The bot interacts with users in Telegram Messenger, helping them track prices, manage sale sheets, and compare items across different shops. The system leverages AWS services like S3 for file storage, DynamoDB for storing user preferences and tracking data, and Lambda functions for real-time event handling. Below is a breakdown of how the bot operates:

1. **User Interaction Flow**
    - **Start Command (`/start`)**: The bot welcomes new users, guiding them through language selection and shop tracking setup. Returning users are taken directly to the main menu.

<p align="center">
  <img src="https://drive.google.com/uc?export=view&id=1OstEV8fvUoA4sQS50d6QUGv8En1yrGqK" width="200" height="400">
  <img src="https://drive.google.com/uc?export=view&id=1-8KtDn0ak2OPikvU-npX9ShUkVgxFMCD" width="200" height="400">
  <img src="https://drive.google.com/uc?export=view&id=1551NCdRtcIxJS0j4S2KeqycOVBndQZb-" width="200" height="400">
</p>

2. **Main Menu Options**
    - **🔍 Search for Item**: Users can search for specific items across shops, receiving item details including prices and images (if enabled).
    - **🛒 Add Shop Item to Track Price**: Users can add items to a tracking list. The bot monitors these items and notifies the user when they are on sale.
    - **🛍 Compare Shopping List Over Shops**: Users can compare prices of items across different shops by selecting shops and entering their shopping list.
    - **⚙️ Settings**: Allows users to manage preferences like excluding or including shops, toggling sale sheet PDF, enabling/disabling item photo groups, and adjusting language settings.
    - **ℹ️ About Project**: Provides information about the bot and its purpose.

3. **Settings Menu**
    - Users can exclude/include shops for tracking, manage their tracked items, toggle options like item photo groups, and change the interface language.

4. **Shop Selection and Item Tracking**
    - The bot ensures users include at least one shop for tracking. When an item is added to the tracking list, the bot monitors the item’s price and notifies the user when it goes on sale.

5. **Search and N-Gram Matching**
    - The bot uses n-gram matching to find items by searching for flexible name variations in the **DynamoDB `detected_data_table`**.

6. **Media Handling**
    - The bot can send item images in media groups (albums) through Telegram, allowing users to view products along with pricing information.

7. **State Management**
    - The bot saves user preferences and interaction states in **DynamoDB**, ensuring a seamless user experience across sessions.
        - **State Saving**: The bot saves the user’s current state (e.g., searching, tracking) to resume interaction seamlessly.
        - **Shop Selection History**: Maintains a history of selected shops, making it easy for users to reselect shops in the future.

8. **AWS S3 and DynamoDB Integration**
    - The bot downloads files from **S3** and processes item images and sale sheets. **DynamoDB** is used to store and retrieve user preferences, tracked items, shop selection history, and other related data.

### User Preferences Table

The **DynamoDB** table storing user preferences includes various attributes to personalize the shopping experience for each user:

| Attribute               | Type   | Description                                    |
|-------------------------|--------|------------------------------------------------|
| **chat_id**              | String | The unique identifier for the user in Telegram |
| **excluded_shops**       | List   | List of shops excluded from tracking           |
| **item_list**            | List   | Items the user has added to their shopping list|
| **language**             | String | User’s preferred language for bot interaction  |
| **photo_group_enabled**  | Bool   | Whether item photos should be sent as media groups |
| **selected_shops**       | List   | Shops selected by the user for tracking        |
| **selected_shops_history** | List | History of selected shops for easy re-selection|
| **state**                | String | Current state of the user in the bot’s flow    |
| **text_info_enabled**    | Bool   | Whether text information is enabled for items  |
| **tracked_items**        | List   | Items the user is currently tracking           |

#### Example Data:

| **chat_id** | **excluded_shops**              | **item_list** | **language** | **photo_group_enabled** | **selected_shops**                         | **selected_shops_history**               | **state** | **text_info_enabled** | **tracked_items** |
|-------------|---------------------------------|---------------|--------------|-------------------------|--------------------------------------------|------------------------------------------|-----------|-----------------------|------------------|
| 825063***   | [Albert Hypermarket]            | []            | en           | true                    | [Albert Supermarket, Albert Hypermarket]   | [Albert Supermarket, Albert Hypermarket] | null      | false                 | []               |
| 437792***   | []                              | []            | en           | true                    | []                                         | [Albert Hypermarket, Albert Supermarket] | null      | true                  | [Pizza]          |
| 508803***   | [Albert Hypermarket]            | []            | en           | true                    | []                                         | null                                     | false     | []                   |
---

### Project Summary and Future Plans

I started this project in the spring, following a full development lifecycle—from idea conception to building a working prototype of the bot. This project has helped me improve my skills in software engineering and MLOps.

#### Future Plans:
- **Expand Language Support**: Currently, the UI only supports English, and item search works in Czech. I plan to support more languages.
- **Enhanced Search**: I plan to add search by item description (models are already trained for detecting all fields). The bot will also find items by related keywords (e.g., searching for "pivo" will return results for "Pilsner Urquell").
- **Improve Name and Price Processing**: I’ve already built a system to handle OCR errors, such as misspelled words or concatenated strings. I need a larger dictionary to enhance this further. I also collect unique OCR price detection scenarios and use regular expressions to process them, but I may introduce a lightweight LLM or fine-tune an existing one to improve this.
- **Additional Features**: There are many other features I plan to implement as the project evolves.
