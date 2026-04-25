package extend

import (
	"io"
	"net/http"
	"strings"
	"testing"
)

type roundTripFunc func(*http.Request) (*http.Response, error)

func (f roundTripFunc) RoundTrip(req *http.Request) (*http.Response, error) {
	return f(req)
}

func TestGetTHSDayKline(t *testing.T) {
	originalURLFormat := thsDayKlineURLFormat
	originalClient := thsHTTPClient
	defer func() {
		thsDayKlineURLFormat = originalURLFormat
		thsHTTPClient = originalClient
	}()

	thsDayKlineURLFormat = "http://example.com/v6/line/hs_%s/0%d/all.js"
	thsHTTPClient = &http.Client{
		Transport: roundTripFunc(func(req *http.Request) (*http.Response, error) {
			body := `quotebridge_v6_line_00_0({"total":2,"sortYear":[[2026,2]],"priceFactor":"1000","price":"1000,100,200,150,1100,110,210,160","dates":"0401,0402","volumn":"100,200"})`
			return &http.Response{
				StatusCode: http.StatusOK,
				Body:       io.NopCloser(strings.NewReader(body)),
				Header:     make(http.Header),
				Request:    req,
			}, nil
		}),
	}

	ls, err := GetTHSDayKline("sz000001", THS_HFQ)
	if err != nil {
		t.Fatalf("GetTHSDayKline() error = %v", err)
	}
	if len(ls) != 2 {
		t.Fatalf("expected 2 klines, got %d", len(ls))
	}
	if got := ls[0].Code; got != "sz000001" {
		t.Fatalf("expected code sz000001, got %s", got)
	}
	if got := ls[0].Close.Int64(); got != 1150 {
		t.Fatalf("expected first close 1150, got %d", got)
	}
	if got := ls[1].Volume; got != 2 {
		t.Fatalf("expected second volume 2, got %d", got)
	}
}
