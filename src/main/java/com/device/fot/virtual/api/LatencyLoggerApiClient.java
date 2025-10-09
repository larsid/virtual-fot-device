package com.device.fot.virtual.api;

import com.device.fot.virtual.model.LatencyRecord;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.ArrayList;
import org.json.JSONArray;
import org.json.JSONObject;

/**
 *
 * @author Uellington Damasceno
 */
public class LatencyLoggerApiClient {

    private final HttpClient client;
    private final String url;

    public LatencyLoggerApiClient(String url) {
        this.url = url;
        this.client = HttpClient.newHttpClient();
    }

    public HttpResponse<String> post(LatencyRecord body) throws IOException, InterruptedException {
        String json = new JSONObject(body).toString();
        HttpRequest request = this.createRequest(json);
        return client.send(request, HttpResponse.BodyHandlers.ofString());
    }

    public HttpResponse<String> postAllLatencies(ArrayList<LatencyRecord> latencyLines) throws IOException, InterruptedException {
        String jsonArray = new JSONArray(latencyLines).toString();
        HttpRequest request = this.createRequest(jsonArray);
        return client.send(request, HttpResponse.BodyHandlers.ofString());
    }

    private HttpRequest createRequest(String json) {
        return HttpRequest.newBuilder()
                .uri(URI.create(this.url))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(json))
                .build();
    }
}
