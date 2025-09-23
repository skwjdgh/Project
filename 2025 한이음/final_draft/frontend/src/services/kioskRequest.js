// STT 결과 텍스트를 서버에 보내고 화면 전환 결정 (기존 handleRequest 로직 분리)
export async function routeKioskRequest(text) {
    const res = await fetch("http://localhost:8000/receive-text/", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({text}),
    });
    if (!res.ok) throw new Error(`서버 응답 오류: ${res.status}`);


    const data = await res.json();
    const summary = data.summary || text;
    const purpose = data.purpose || "";


    if (summary.includes("축제") || summary.includes("행사")) {
        return {screen: "FESTIVAL", purpose, payload: {keyword: text}};
    }


    if (summary.includes("날씨")) {
        const weatherRes = await fetch("http://localhost:8000/weather/", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({city: "Seoul"}),
        });
        if (!weatherRes.ok) {
            const t = await weatherRes.text();
            throw new Error(`날씨 API 오류: ${weatherRes.status} ${t}`);
        }
        const weatherResult = await weatherRes.json();
        return {
            screen: "WEATHER_VIEW",
            purpose,
            payload: {
                keyword: text,
                weatherData: JSON.stringify(weatherResult, null, 2),
                weatherAiSummary: weatherResult?._meta?.ai_summary_ko ?? "",
            },
        };
    }


    let docName = "";
    if (summary.includes("등본")) docName = "주민등록등본";
    else if (summary.includes("초본")) docName = "주민등록초본";
    else if (summary.includes("가족관계")) docName = "가족관계증명서";
    else if (summary.includes("건강보험")) docName = "건강보험자격득실확인서";


    if (docName) return {screen: "PIN_INPUT", purpose: docName, payload: {}};
    return {screen: "UNRECOGNIZED", purpose: "", payload: {}};
}