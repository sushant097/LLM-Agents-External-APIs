from gsuite_clients import create_or_replace_sheet, send_email_with_sheet_link

if __name__ == "__main__":
    header = ["Pos", "Driver", "Team", "Points"]
    rows = [
        ["1", "Test Driver", "Test Team", "123"],
        ["2", "Another Driver", "Another Team", "110"],
    ]

    print("Creating test sheet...")
    result = create_or_replace_sheet(
        title="TEST F1 Standings (Debug)",
        header=header,
        rows=rows,
    )
    print("Sheet created:", result["spreadsheetUrl"])

    print("Sending email...")
    status = send_email_with_sheet_link(
        to_email="your_gmail@gmail.com",
        subject="Debug F1 Sheet Link",
        sheet_url=result["spreadsheetUrl"],
        message="This is a debug email from gsuite_clients.py",
    )
    print(status)
    print("Email sent.")