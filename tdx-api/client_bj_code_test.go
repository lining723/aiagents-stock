package tdx

import (
	"errors"
	"io"
	"net/http"
	"net/url"
	"strings"
	"testing"
)

type roundTripFunc func(*http.Request) (*http.Response, error)

func (f roundTripFunc) RoundTrip(req *http.Request) (*http.Response, error) {
	return f(req)
}

func TestGetBjCodesRetryOnBadRecordMAC(t *testing.T) {
	originalURL := bjCodesURL
	originalFactory := bjHTTPClientFactory
	defer func() {
		bjCodesURL = originalURL
		bjHTTPClientFactory = originalFactory
	}()

	bjCodesURL = "https://example.com/nqhq_en.do?callback=jQuery3710848510589806625_%d"

	attempts := 0
	bjHTTPClientFactory = func() *http.Client {
		return &http.Client{
			Transport: roundTripFunc(func(req *http.Request) (*http.Response, error) {
				attempts++
				if attempts == 1 {
					return nil, &url.Error{
						Op:  http.MethodPost,
						URL: req.URL.String(),
						Err: errors.New("remote error: tls: bad record MAC"),
					}
				}

				body := `jQuery3710848510589806625_1([{"content":[{"hqjsrq":"2026-04-15","hqzqdm":"430001","hqzqjc":"测试股票","hqzrsp":10,"hqjrkp":10,"hqzgcj":11,"hqzdcj":9,"hqzjcj":10.5,"hqcjsl":1000,"hqcjje":10500}],"totalElements":1,"totalPages":1,"lastPage":true}])`
				return &http.Response{
					StatusCode: http.StatusOK,
					Body:       io.NopCloser(strings.NewReader(body)),
					Header:     make(http.Header),
					Request:    req,
				}, nil
			}),
		}
	}

	codes, err := GetBjCodes()
	if err != nil {
		t.Fatalf("GetBjCodes() error = %v", err)
	}
	if attempts != 2 {
		t.Fatalf("expected 2 attempts, got %d", attempts)
	}
	if len(codes) != 1 {
		t.Fatalf("expected 1 code, got %d", len(codes))
	}
	if codes[0].Code != "430001" {
		t.Fatalf("expected code 430001, got %s", codes[0].Code)
	}
}
