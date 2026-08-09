import { useEffect } from 'react'

import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import {
    Link,
    useNavigate,
    useParams,
} from 'react-router-dom'

import {
    useCreateMonitor,
    useMonitor,
    useUpdateMonitor,
} from '../features/monitors/queries.ts'
import {
    monitorCreateSchema,
    type MonitorCreateFormValues,
} from '../features/monitors/schemas.ts'
import { ApiError } from '../services/api/client.ts'

interface CreateMonitorPageProps {
    mode?: 'create' | 'edit'
}

function getMonitorMutationError(error: unknown) {
    if (error instanceof ApiError) {
        return error.message
    }

    return 'Unable to save the monitor. Please try again.'
}

export function CreateMonitorPage({
    mode = 'create',
}: CreateMonitorPageProps) {
    const navigate = useNavigate()
    const { monitorId = '' } = useParams()
    const isEditing = mode === 'edit'
    const monitorQuery = useMonitor(
        isEditing ? monitorId : '',
    )
    const createMonitor = useCreateMonitor()
    const updateMonitor = useUpdateMonitor()
    const {
        register,
        handleSubmit,
        reset,
        setError,
        formState: {
            errors,
            isSubmitting,
        },
    } = useForm<MonitorCreateFormValues>({
        resolver: zodResolver(monitorCreateSchema),
        defaultValues: {
            name: '',
            url: 'https://',
            interval_seconds: 60,
            timeout_seconds: 5,
            expected_status: 200,
            failure_threshold: 3,
            recovery_threshold: 2,
        },
    })

    useEffect(() => {
        const monitor = monitorQuery.data

        if (!isEditing || !monitor) {
            return
        }

        reset({
            name: monitor.name,
            url: monitor.url,
            interval_seconds: monitor.interval_seconds,
            timeout_seconds: monitor.timeout_seconds,
            expected_status: monitor.expected_status,
            failure_threshold: monitor.failure_threshold,
            recovery_threshold: monitor.recovery_threshold,
        })
    }, [isEditing, monitorQuery.data, reset])

    async function submit(values: MonitorCreateFormValues) {
        try {
            if (isEditing) {
                await updateMonitor.mutateAsync({
                    monitorId,
                    input: {
                        ...values,
                        method: 'GET',
                    },
                })
                navigate(`/monitors/${monitorId}`, {
                    replace: true,
                })
                return
            }

            await createMonitor.mutateAsync({
                ...values,
                method: 'GET',
            })
            navigate('/monitors', { replace: true })
        } catch (error) {
            setError('root', {
                message: getMonitorMutationError(error),
            })
        }
    }

    const pageTitle = isEditing
        ? 'Edit monitor'
        : 'Create monitor'
    const pageDescription = isEditing
        ? 'Update how PulseWatch checks this website or API.'
        : 'Configure how PulseWatch should check your website or API.'
    const cancelDestination = isEditing
        ? `/monitors/${monitorId}`
        : '/monitors'

    if (isEditing && monitorQuery.isPending) {
        return <p aria-live="polite">Loading monitor...</p>
    }

    if (isEditing && monitorQuery.isError) {
        return (
            <section className="error-state" role="alert">
                <h1>Unable to load monitor</h1>
                <p>The monitor may not exist or may not belong to you.</p>
                <Link className="button button--secondary" to="/monitors">
                    Back to monitors
                </Link>
            </section>
        )
    }


    return (
        <section
            className="form-page"
            aria-labelledby="monitor-form-title"
        >
            <header>
                <p className="page-eyebrow">Endpoint management</p>
                <h1 id="monitor-form-title">{pageTitle}</h1>
                <p className="page-description">
                    {pageDescription}
                </p>
            </header>

            <form
                className="monitor-form"
                noValidate
                onSubmit={handleSubmit(submit)}
            >
                {errors.root?.message ? (
                    <div className="form-alert" role="alert">
                        {errors.root.message}
                    </div>
                ) : null}

                <div className="form-field">
                    <label htmlFor="monitor-name">Monitor name</label>
                    <input
                        {...register('name')}
                        aria-invalid={Boolean(errors.name)}
                        autoComplete="off"
                        id="monitor-name"
                        placeholder="Production API"
                    />
                    {errors.name?.message ? (
                        <p className="form-error">{errors.name.message}</p>
                    ) : null}
                </div>

                <div className="form-field">
                    <label htmlFor="monitor-url">URL</label>
                    <input
                        {...register('url')}
                        aria-invalid={Boolean(errors.url)}
                        autoComplete="url"
                        id="monitor-url"
                        inputMode="url"
                        placeholder="https://api.example.com/health"
                        type="url"
                    />
                    {errors.url?.message ? (
                        <p className="form-error">{errors.url.message}</p>
                    ) : null}
                </div>

                <div className="monitor-form__grid">
                    <div className="form-field">
                        <label htmlFor="monitor-interval">
                            Interval (seconds)
                        </label>
                        <input
                            {...register('interval_seconds', {
                                valueAsNumber: true,
                            })}
                            aria-invalid={Boolean(errors.interval_seconds)}
                            id="monitor-interval"
                            max="86400"
                            min="30"
                            type="number"
                        />
                        {errors.interval_seconds?.message ? (
                            <p className="form-error">
                                {errors.interval_seconds.message}
                            </p>
                        ) : null}
                    </div>

                    <div className="form-field">
                        <label htmlFor="monitor-timeout">
                            Timeout (seconds)
                        </label>
                        <input
                            {...register('timeout_seconds', {
                                valueAsNumber: true,
                            })}
                            aria-invalid={Boolean(errors.timeout_seconds)}
                            id="monitor-timeout"
                            max="60"
                            min="1"
                            type="number"
                        />
                        {errors.timeout_seconds?.message ? (
                            <p className="form-error">
                                {errors.timeout_seconds.message}
                            </p>
                        ) : null}
                    </div>

                    <div className="form-field">
                        <label htmlFor="expected-status">
                            Expected status
                        </label>
                        <input
                            {...register('expected_status', {
                                valueAsNumber: true,
                            })}
                            aria-invalid={Boolean(errors.expected_status)}
                            id="expected-status"
                            max="599"
                            min="100"
                            type="number"
                        />
                        {errors.expected_status?.message ? (
                            <p className="form-error">
                                {errors.expected_status.message}
                            </p>
                        ) : null}
                    </div>

                    <div className="form-field">
                        <label htmlFor="failure-threshold">
                            Failure threshold
                        </label>
                        <input
                            {...register('failure_threshold', {
                                valueAsNumber: true,
                            })}
                            aria-invalid={Boolean(errors.failure_threshold)}
                            id="failure-threshold"
                            max="10"
                            min="1"
                            type="number"
                        />
                    </div>

                    <div className="form-field">
                        <label htmlFor="recovery-threshold">
                            Recovery threshold
                        </label>
                        <input
                            {...register('recovery_threshold', {
                                valueAsNumber: true,
                            })}
                            aria-invalid={Boolean(errors.recovery_threshold)}
                            id="recovery-threshold"
                            max="10"
                            min="1"
                            type="number"
                        />
                    </div>
                </div>

                <div className="form-actions">
                    <Link
                        className="button button--secondary"
                        to={cancelDestination}
                    >
                        Cancel
                    </Link>
                    <button
                        className="button button--primary"
                        disabled={isSubmitting}
                        type="submit"
                    >
                        {isSubmitting
                            ? 'Saving...'
                            : isEditing
                                ? 'Save changes'
                                : 'Create monitor'}
                    </button>
                </div>
            </form>
        </section>
    )
}