{{- define "bizinsight.name" -}}
{{- .Chart.Name }}
{{- end }}

{{- define "bizinsight.fullname" -}}
{{- printf "%s" .Release.Name }}
{{- end }}

{{- define "bizinsight.labels" -}}
app.kubernetes.io/name: {{ include "bizinsight.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}

{{- define "bizinsight.selectorLabels" -}}
app.kubernetes.io/name: {{ include "bizinsight.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

