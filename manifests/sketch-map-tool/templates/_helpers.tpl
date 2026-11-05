{{/*
Expand the name of the chart.
*/}}
{{- define "sketch-map-tool.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "sketch-map-tool.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "sketch-map-tool.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "sketch-map-tool.labels" -}}
helm.sh/chart: {{ include "sketch-map-tool.chart" . }}
{{ include "sketch-map-tool.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "sketch-map-tool.selectorLabels" -}}
app.kubernetes.io/name: {{ include "sketch-map-tool.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "sketch-map-tool.postgresVars" -}}
- name: SMT_POSTGRES_HOST
  value: {{ ternary (printf "%s-postgres" .Release.Name) .Values.postgres.external.host .Values.postgres.enabled }}
{{- with .Values.postgres.external.port }}
- name: SMT_POSTGRES_PORT
  value: {{ quote .Values.postgres.external.port }}
{{- end }}
- name: SMT_POSTGRES_DBNAME
  {{- if .Values.postgres.enabled }}
  {{- if .Values.postgres.userDatabase.name.secretKey }}
  valueFrom:
    secretKeyRef:
      key: {{ .Values.postgres.userDatabase.name.secretKey }}
      name: {{ .Values.postgres.userDatabase.existingSecret }}
  {{- else }}
  value: {{ .Values.postgres.userDatabase.name.value }}
  {{- end }}
  {{- else }}
  value: {{ .Values.postgres.external.database }}
  {{- end }}
- name: SMT_POSTGRES_USER
  {{- if .Values.postgres.enabled }}
  {{- if .Values.postgres.userDatabase.user.secretKey }}
  valueFrom:
  secretKeyRef:
    key: {{ .Values.postgres.userDatabase.user.secretKey }}
    name: {{ .Values.postgres.userDatabase.existingSecret }}
  {{- else }}
  value: {{ .Values.postgres.userDatabase.user.value }}
  {{- end }}
  {{- else }}
  value: {{ .Values.postgres.external.user }}
  {{- end }}
- name: SMT_POSTGRES_PASSWORD
  {{- if .Values.postgres.enabled }}
  {{- if .Values.postgres.userDatabase.password.secretKey }}
  valueFrom:
  secretKeyRef:
    key: {{ .Values.postgres.userDatabase.password.secretKey }}
    name: {{ .Values.postgres.userDatabase.existingSecret }}
  {{- else }}
  value: {{ .Values.postgres.userDatabase.password.value }}
  {{- end }}
  {{- else }}
  value: {{ .Values.postgres.external.password }}
  {{- end }}
{{- end }}

{{- define "sketch-map-tool.redisVars" -}}
- name: SMT_REDIS_HOST
  value: {{ ternary (printf "%s-redis" .Release.Name) .Values.redis.external.host .Values.redis.enabled }}
{{- with .Values.redis.external.port }}
- name: SMT_REDIS_PORT
  value: {{ quote .Values.redis.external.port }}
{{- end }}
{{- if not .Values.redis.enabled }}
{{- with .Values.redis.external.dbNumber }}
- name: SMT_REDIS_DB_NUMBER
  value: {{ quote .Values.redis.external.dbNumber }}
{{- end }}
{{- with .Values.redis.external.username }}
- name: SMT_REDIS_USERNAME
  value: {{ quote .Values.redis.external.username }}
{{- end }}
{{- with .Values.redis.external.password }}
- name: SMT_REDIS_PASSWORD
  value: {{ quote .Values.redis.external.password }}
{{- end }}
{{- end }}
{{- end }}
