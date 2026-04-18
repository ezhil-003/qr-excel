class UpiQrAdd < Formula
  desc "Interactive CLI tool for adding decorated UPI QR codes to Excel rows"
  homepage "https://github.com/ezhil-003/qr-excel"
  url "https://github.com/ezhil-003/qr-excel/releases/download/<VERSION>/upi-qr-add-macos-universal"
  version "<VERSION>"
  sha256 "<GENERATE_SHA256_HASH_OF_THE_DOWNLOADED_FILE>" # Update this with the sha256 of the binary

  def install
    # Rename the downloaded binary to upi-qr-add
    bin.install "upi-qr-add-macos-universal" => "upi-qr-add"
  end

  test do
    system "#{bin}/upi-qr-add", "--help"
  end
end
