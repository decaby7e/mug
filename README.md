# Mug

Print accounting software for CUPS (a replacement to Pykota)

## CUPS Administration Notes

To manually set PPD for printer in the case that the web GUI doesn't like Mug's
`device-uri`:

```sh
lpadmin -P /etc/cups/ppd/Virtual_PDF_Printer.ppd -d MugPDF
```
